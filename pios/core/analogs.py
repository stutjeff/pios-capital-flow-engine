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
    minimum_coverage = float(cfg.get("minimum_coverage_pct", 55))
    top_n = int(cfg.get("top_n", 3))
    next_horizon = int(cfg.get("next_stage_horizon_days", 10))

    if not library_path.exists():
        return {"available": False, "reason": "analog library not built", "matches": []}
    try:
        library = json.loads(library_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "reason": f"invalid library: {exc}", "matches": []}
    if history.empty:
        return {"available": False, "reason": "risk history empty", "matches": []}

    latest = history.iloc[-1]
    current = pd.to_numeric(history["risk_score"], errors="coerce").dropna().tail(lookback).values
    matches: list[dict[str, Any]] = []

    for event in library.get("events", []):
        phase = _best_phase(current, event, lookback)
        trajectory_score = phase.get("trajectory_pct")
        profile = event.get("component_profile", {})

        # When the library has daily component series, use the profile around the matched phase.
        phase_index = phase.get("phase_index")
        component_series = event.get("component_series", {})
        if phase_index is not None and component_series:
            dynamic_profile = {}
            for column in VECTOR_COLS[1:]:
                series = component_series.get(column, [])
                if phase_index < len(series):
                    dynamic_profile[column] = series[phase_index]
            if dynamic_profile:
                profile = dynamic_profile

        component_score, coverage = _component_similarity(latest, profile)
        if pd.isna(trajectory_score) and pd.isna(component_score):
            continue
        score = (0 if pd.isna(trajectory_score) else trajectory_score) * 0.65 + (0 if pd.isna(component_score) else component_score) * 0.35
        total_coverage = min(100.0, (coverage + float(event.get("coverage_pct", 0))) / 2)
        if total_coverage < minimum_coverage:
            continue

        next_stage = _next_stage(event, phase_index, next_horizon)
        matches.append({
            "id": event.get("id"),
            "label": event.get("label"),
            "similarity_pct": round(score, 1),
            "trajectory_pct": round(trajectory_score, 1) if pd.notna(trajectory_score) else None,
            "component_pct": round(component_score, 1) if pd.notna(component_score) else None,
            "coverage_pct": round(total_coverage, 1),
            "reference_start": event.get("start"),
            "reference_end": event.get("end"),
            "phase_day": phase.get("phase_day"),
            "phase_date": phase.get("phase_date"),
            "next_stage": next_stage,
        })

    matches.sort(key=lambda x: x["similarity_pct"], reverse=True)
    return {
        "available": bool(matches),
        "reason": "" if matches else "no match meets coverage",
        "matches": matches[:top_n],
        "built_at": library.get("built_at"),
        "library_version": library.get("version"),
    }
