from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import load_yaml

VECTOR_COLS = ["risk_score", "credit_score", "volatility_score", "dollar_rates_score", "risk_asset_score", "defensive_score"]


def _normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return x
    mean = np.nanmean(x)
    std = np.nanstd(x)
    return (x - mean) / std if std > 1e-9 else x - mean


def _trajectory_similarity(a: np.ndarray, b: np.ndarray) -> float:
    n = min(len(a), len(b))
    if n < 5:
        return float("nan")
    aa = _normalize(np.asarray(a[-n:], dtype=float))
    bb = _normalize(np.asarray(b[-n:], dtype=float))
    rmse = float(np.sqrt(np.mean((aa - bb) ** 2)))
    return max(0.0, 100.0 * (1.0 - rmse / 3.0))


def _component_similarity(latest: pd.Series, profile: dict[str, float]) -> tuple[float, float]:
    common: list[tuple[float, float]] = []
    for column in VECTOR_COLS[1:]:
        if column in profile and pd.notna(latest.get(column)):
            common.append((float(latest[column]), float(profile[column])))
    if not common:
        return float("nan"), 0.0
    a = np.array([x[0] for x in common])
    b = np.array([x[1] for x in common])
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    cosine = float(np.dot(a, b) / denom) if denom else 0.0
    return max(0.0, min(100.0, (cosine + 1) * 50)), len(common) / (len(VECTOR_COLS) - 1) * 100


def _best_phase(current: np.ndarray, event: dict[str, Any], lookback: int) -> dict[str, Any]:
    trajectory = np.asarray(event.get("risk_trajectory", []), dtype=float)
    dates = event.get("dates", [])
    if len(trajectory) < 5:
        return {"trajectory_pct": float("nan"), "phase_day": None, "phase_date": None}

    current = np.asarray(current, dtype=float)
    window = min(lookback, len(current), len(trajectory))
    if window < 5:
        return {"trajectory_pct": float("nan"), "phase_day": None, "phase_date": None}

    best_score = -1.0
    best_end = window - 1
    for end in range(window - 1, len(trajectory)):
        reference = trajectory[end - window + 1:end + 1]
        score = _trajectory_similarity(current[-window:], reference)
        if pd.notna(score) and score > best_score:
            best_score = score
            best_end = end

    phase_date = dates[best_end] if best_end < len(dates) else None
    return {
        "trajectory_pct": best_score if best_score >= 0 else float("nan"),
        "phase_day": best_end + 1,
        "phase_date": phase_date,
        "phase_index": best_end,
    }


def _next_stage(event: dict[str, Any], phase_index: int | None, horizon: int = 10) -> dict[str, Any]:
    if phase_index is None:
        return {}
    trajectory = np.asarray(event.get("risk_trajectory", []), dtype=float)
    if len(trajectory) <= phase_index + 1:
        return {"available": False, "reason": "已接近參考事件尾端"}

    future_end = min(len(trajectory) - 1, phase_index + horizon)
    current = float(trajectory[phase_index])
    future = float(trajectory[future_end])
    peak = float(np.nanmax(trajectory[phase_index + 1:future_end + 1]))
    trough = float(np.nanmin(trajectory[phase_index + 1:future_end + 1]))
    delta = future - current
    max_worsening = peak - current
    max_improving = trough - current

    if max_worsening >= 8:
        direction = "明顯惡化"
    elif delta >= 3:
        direction = "逐步惡化"
    elif max_improving <= -8:
        direction = "明顯改善"
    elif delta <= -3:
        direction = "逐步改善"
    else:
        direction = "高檔震盪"

    components = event.get("component_series", {})
    changes: list[tuple[str, float]] = []
    labels = {
        "credit_score": "信用市場",
        "volatility_score": "波動率",
        "dollar_rates_score": "美元與利率",
        "risk_asset_score": "風險資產撤退",
        "defensive_score": "避險輪動",
    }
    for column, series in components.items():
        if phase_index < len(series) and future_end < len(series):
            try:
                changes.append((labels.get(column, column), float(series[future_end]) - float(series[phase_index])))
            except (TypeError, ValueError):
                continue
    changes.sort(key=lambda x: x[1], reverse=True)
    leading = [f"{name}{delta_value:+.1f}" for name, delta_value in changes[:3] if abs(delta_value) >= 0.5]

    return {
        "available": True,
        "horizon_days": future_end - phase_index,
        "direction": direction,
        "risk_change": round(delta, 1),
        "max_worsening": round(max_worsening, 1),
        "leading_components": leading,
    }


def compare(history: pd.DataFrame, library_path: Path) -> dict[str, Any]:
    cfg = load_yaml("state_engine.yaml").get("historical_analogs", {})
    lookback = int(cfg.get("lookback_days", 20))
    minimum_coverage = float(cfg.get("minimum_coverage_pct", 25))
    top_n = int(cfg.get("top_n", 3))
    next_horizon = int(cfg.get("next_stage_horizon_days", 10))

    if not library_path.exists():
        return {"available": False, "reason": "analog library not built", "reason_zh":"類比庫不存在", "matches": [], "rebuild_recommended":True}
    try:
        library = json.loads(library_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "reason": f"invalid library: {exc}", "reason_zh":"類比庫格式損壞", "matches": [], "rebuild_recommended":True}
    if history.empty:
        return {"available": False, "reason": "risk history empty", "reason_zh":"目前風險歷史為空", "matches": [], "rebuild_recommended":False}

    events=library.get("events", [])
    built_events=sum(1 for e in events if e.get('status') in {'OK','PARTIAL'})
    usable_events=sum(1 for e in events if len(e.get('risk_trajectory',[]) or [])>=5)
    diagnostics={
        'library_version':library.get('version'), 'total_events':len(events),
        'built_events':built_events, 'usable_events':usable_events,
        'event_statuses':{str(e.get('id')):str(e.get('status','UNKNOWN')) for e in events},
    }

    latest = history.iloc[-1]
    current = pd.to_numeric(history["risk_score"], errors="coerce").dropna().tail(lookback).values
    matches: list[dict[str, Any]] = []
    rejected=[]

    for event in events:
        if len(event.get('risk_trajectory',[]) or []) < 5:
            rejected.append({'id':event.get('id'),'reason':'NO_TRAJECTORY'})
            continue
        phase = _best_phase(current, event, lookback)
        trajectory_score = phase.get("trajectory_pct")
        profile = event.get("component_profile", {})
        phase_index = phase.get("phase_index")
        component_series = event.get("component_series", {})
        if phase_index is not None and component_series:
            dynamic_profile = {}
            for column in VECTOR_COLS[1:]:
                series = component_series.get(column, [])
                if phase_index < len(series) and series[phase_index] is not None:
                    dynamic_profile[column] = series[phase_index]
            if dynamic_profile:
                profile = dynamic_profile

        component_score, component_coverage = _component_similarity(latest, profile)
        trajectory_available=pd.notna(trajectory_score)
        component_available=pd.notna(component_score)
        if not trajectory_available and not component_available:
            rejected.append({'id':event.get('id'),'reason':'NO_COMPARABLE_FEATURE'})
            continue

        # Adaptive weighting: trajectory alone is allowed when old component data is
        # unavailable. It is explicitly labelled lower confidence rather than discarded.
        if trajectory_available and component_available:
            score=float(trajectory_score)*0.65+float(component_score)*0.35
            comparison_mode='TRAJECTORY_AND_COMPONENTS'
        elif trajectory_available:
            score=float(trajectory_score)
            comparison_mode='TRAJECTORY_ONLY'
        else:
            score=float(component_score)
            comparison_mode='COMPONENTS_ONLY'

        event_coverage=float(event.get('coverage_pct',0) or 0)
        trajectory_coverage=min(100.0, len(event.get('risk_trajectory',[]))/max(5,lookback)*100)
        total_coverage=(trajectory_coverage*0.6 + component_coverage*0.25 + event_coverage*0.15)
        if total_coverage < minimum_coverage:
            rejected.append({'id':event.get('id'),'reason':'LOW_COVERAGE','coverage_pct':round(total_coverage,1)})
            continue

        next_stage = _next_stage(event, phase_index, next_horizon)
        matches.append({
            "id": event.get("id"), "label": event.get("label"),
            "similarity_pct": round(score, 1),
            "trajectory_pct": round(float(trajectory_score), 1) if trajectory_available else None,
            "component_pct": round(float(component_score), 1) if component_available else None,
            "coverage_pct": round(total_coverage, 1),
            "comparison_mode":comparison_mode,
            "reference_start": event.get("start"), "reference_end": event.get("end"),
            "phase_day": phase.get("phase_day"), "phase_date": phase.get("phase_date"),
            "next_stage": next_stage,
        })

    matches.sort(key=lambda x: x["similarity_pct"], reverse=True)
    diagnostics['rejected']=rejected
    if matches:
        reason=''; reason_zh=''; rebuild=False
    elif usable_events==0:
        reason='library built but no usable historical trajectory'
        reason_zh='類比庫已執行，但歷史資料源沒有產生足夠的可比風險軌跡'
        rebuild=False
    else:
        reason='no match meets adaptive coverage'
        reason_zh='已有歷史軌跡，但目前樣本與可用欄位仍不足以形成可靠類比'
        rebuild=False
    return {
        "available": bool(matches), "reason":reason, "reason_zh":reason_zh,
        "matches": matches[:top_n], "built_at": library.get("built_at"),
        "library_version": library.get("version"), "diagnostics":diagnostics,
        "rebuild_recommended":rebuild,
    }

