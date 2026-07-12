from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import load_yaml

STATE_ORDER = ["NORMAL", "ROTATION", "RISK_OFF", "CREDIT_STRESS", "LIQUIDITY_STRESS", "SYSTEMIC"]
STATE_ZH = {
    "NORMAL": "正常",
    "ROTATION": "板塊輪動",
    "RISK_OFF": "風險撤退",
    "CREDIT_STRESS": "信用壓力",
    "LIQUIDITY_STRESS": "流動性壓力",
    "SYSTEMIC": "系統性風險",
}

MODULES = {
    "credit_score": ("信用市場", 20.0),
    "volatility_score": ("波動率", 15.0),
    "dollar_rates_score": ("美元與利率", 20.0),
    "risk_asset_score": ("風險資產撤退", 25.0),
    "defensive_score": ("避險與防禦輪動", 20.0),
}


def _streak(values: pd.Series, predicate) -> int:
    n = 0
    for value in reversed(values.tolist()):
        if pd.notna(value) and predicate(float(value)):
            n += 1
        else:
            break
    return n


def _slope(values: pd.Series, n: int) -> float:
    x = pd.to_numeric(values, errors="coerce").dropna().tail(n)
    if len(x) < 2:
        return float("nan")
    return float(np.polyfit(np.arange(len(x)), x.values, 1)[0])


def _breadth(latest: pd.Series) -> dict[str, Any]:
    active: list[str] = []
    detail: list[dict[str, Any]] = []
    for column, (label, maximum) in MODULES.items():
        value = float(latest.get(column, 0) or 0)
        ratio = value / maximum if maximum else 0.0
        is_active = ratio >= 0.35
        if is_active:
            active.append(column)
        detail.append({
            "column": column,
            "label": label,
            "score": round(value, 1),
            "max": maximum,
            "ratio_pct": round(ratio * 100, 1),
            "active": is_active,
        })
    pct = len(active) / len(MODULES) * 100
    return {
        "active_modules": active,
        "active_count": len(active),
        "total_modules": len(MODULES),
        "breadth_pct": round(pct, 1),
        "detail": detail,
    }


def _state_candidate(latest: pd.Series, breadth: dict[str, Any], cfg: dict[str, Any]) -> str:
    risk = float(latest.get("risk_score", 0))
    breadth_pct = breadth["breadth_pct"]
    credit = float(latest.get("credit_score", 0))
    vol = float(latest.get("volatility_score", 0))
    defensive = float(latest.get("defensive_score", 0))
    risk_asset = float(latest.get("risk_asset_score", 0))
    thresholds = cfg.get("risk_thresholds", {})

    if risk >= float(thresholds.get("systemic", 75)) and breadth_pct >= 75:
        return "SYSTEMIC"
    if risk >= float(thresholds.get("liquidity_stress", 60)) and breadth_pct >= 60 and vol >= 8 and defensive >= 7:
        return "LIQUIDITY_STRESS"
    if risk >= float(thresholds.get("credit_stress", 48)) and credit >= 12:
        return "CREDIT_STRESS"
    if risk >= float(thresholds.get("risk_off", 35)) and breadth_pct >= float(cfg.get("breadth", {}).get("risk_off_pct", 57)):
        return "RISK_OFF"
    if risk_asset >= 7 or (risk >= float(thresholds.get("observe", 15)) and breadth_pct < 57):
        return "ROTATION"
    return "NORMAL"


def _state_reasons(state: str, latest: pd.Series, breadth: dict[str, Any], persistence: dict[str, int], cfg: dict[str, Any]) -> dict[str, Any]:
    risk = float(latest.get("risk_score", 0))
    credit = float(latest.get("credit_score", 0))
    vol = float(latest.get("volatility_score", 0))
    risk_asset = float(latest.get("risk_asset_score", 0))
    defensive = float(latest.get("defensive_score", 0))
    breadth_pct = float(breadth.get("breadth_pct", 0))
    t = cfg.get("risk_thresholds", {})

    confirmed: list[str] = []
    blockers: list[str] = []

    if risk_asset >= 7:
        confirmed.append(f"風險資產撤退 {risk_asset:.1f}/25 已升溫")
    if credit >= 7:
        confirmed.append(f"信用市場 {credit:.1f}/20 已升溫")
    if vol >= 5.25:
        confirmed.append(f"波動率 {vol:.1f}/15 已升溫")
    if defensive >= 7:
        confirmed.append(f"避險輪動 {defensive:.1f}/20 已升溫")
    if breadth_pct >= 40:
        confirmed.append(f"風險廣度達 {breadth_pct:.0f}%")
    if persistence.get("above_observe", 0) >= 3:
        confirmed.append(f"風險≥15分已持續 {persistence['above_observe']} 天")

    if risk < float(t.get("risk_off", 35)):
        blockers.append(f"總風險尚低於風險撤退門檻 {float(t.get('risk_off', 35)):.0f}")
    if breadth_pct < float(cfg.get("breadth", {}).get("risk_off_pct", 57)):
        blockers.append(f"同步惡化廣度僅 {breadth_pct:.0f}%")
    if credit < 12:
        blockers.append("信用壓力尚未達確認門檻")
    if vol < 8:
        blockers.append("波動率尚未進入壓力區")
    if defensive < 7:
        blockers.append("避險資產尚未形成一致流入")

    if state == "NORMAL":
        summary = "多數核心模組仍在正常區間。"
    elif state == "ROTATION":
        summary = "風險集中於部分板塊，尚未擴散為全面撤退。"
    elif state == "RISK_OFF":
        summary = "多個風險模組同步惡化，市場開始進入廣泛撤退。"
    elif state == "CREDIT_STRESS":
        summary = "信用市場已成為主要壓力來源。"
    elif state == "LIQUIDITY_STRESS":
        summary = "波動、避險與廣度共同確認流動性壓力。"
    else:
        summary = "高風險、廣度與持續性均指向系統性壓力。"

    return {"summary": summary, "confirmed": confirmed[:5], "blockers": blockers[:5]}


def _velocity_metrics(risk: pd.Series) -> dict[str, Any]:
    clean = pd.to_numeric(risk, errors="coerce").dropna()
    if clean.empty:
        return {}
    diff = clean.diff()
    slope3 = _slope(clean, 3)
    slope5 = _slope(clean, 5)
    slope10 = _slope(clean, 10)
    acceleration = float(slope3 - slope10) if pd.notna(slope3) and pd.notna(slope10) else float("nan")
    positive_days_5 = int((diff.tail(5) > 0).sum())
    non_decline_days_7 = int((diff.tail(7) >= -0.25).sum())
    recent = clean.tail(7)
    range_7d = float(recent.max() - recent.min()) if len(recent) else float("nan")
    peak = float(clean.tail(30).max())
    latest = float(clean.iloc[-1])
    off_peak = latest - peak

    if pd.notna(slope5) and slope5 >= 1.0 and acceleration >= 0.25:
        label = "加速累積"
    elif pd.notna(slope5) and slope5 >= 0.25:
        label = "緩慢累積"
    elif pd.notna(slope5) and slope5 <= -1.0:
        label = "快速改善"
    elif pd.notna(slope5) and slope5 <= -0.25:
        label = "逐步改善"
    else:
        label = "橫向震盪"

    return {
        "daily_velocity_3d": round(slope3, 2) if pd.notna(slope3) else None,
        "daily_velocity_5d": round(slope5, 2) if pd.notna(slope5) else None,
        "daily_velocity_10d": round(slope10, 2) if pd.notna(slope10) else None,
        "acceleration": round(acceleration, 2) if pd.notna(acceleration) else None,
        "positive_days_5": positive_days_5,
        "non_decline_days_7": non_decline_days_7,
        "range_7d": round(range_7d, 1) if pd.notna(range_7d) else None,
        "off_30d_peak": round(off_peak, 1),
        "label": label,
    }


def evaluate_state(history: pd.DataFrame, previous_state: str | None = None) -> dict[str, Any]:
    cfg = load_yaml("state_engine.yaml")
    if history is None or history.empty:
        return {"state": "NORMAL", "state_zh": STATE_ZH["NORMAL"], "reason": "風險歷史不足"}

    h = history.copy()
    for column in h.columns:
        if column not in {"date", "mode"}:
            h[column] = pd.to_numeric(h[column], errors="coerce")
    latest = h.iloc[-1]
    breadth = _breadth(latest)
    candidate = _state_candidate(latest, breadth, cfg)
    risk = h["risk_score"]

    momentum_1d = float(risk.iloc[-1] - risk.iloc[-2]) if len(risk) >= 2 else float("nan")
    momentum_3d = float(risk.iloc[-1] - risk.iloc[-4]) if len(risk) >= 4 else float("nan")
    momentum_5d = float(risk.iloc[-1] - risk.iloc[-6]) if len(risk) >= 6 else float("nan")
    slope5 = _slope(risk, 5)
    slope10 = _slope(risk, 10)
    thresholds = cfg.get("risk_thresholds", {})
    diff = risk.diff().fillna(0)
    persistence = {
        "above_observe": _streak(risk, lambda x: x >= float(thresholds.get("observe", 15))),
        "above_alert": _streak(risk, lambda x: x >= float(thresholds.get("alert", 25))),
        "above_risk_off": _streak(risk, lambda x: x >= float(thresholds.get("risk_off", 35))),
        "non_decreasing": _streak(diff, lambda x: x >= -0.25),
        "strictly_rising": _streak(diff, lambda x: x > 0),
        "improving": _streak(diff, lambda x: x < 0),
    }

    valid_risk = risk.dropna()
    percentile = float((valid_risk <= valid_risk.iloc[-1]).mean() * 100) if len(valid_risk) >= 20 else float("nan")
    rank = int((valid_risk > valid_risk.iloc[-1]).sum() + 1) if len(valid_risk) else 0
    previous = previous_state if previous_state in STATE_ORDER else None
    state = candidate
    transition_note = "候選狀態直接採用"
    if previous:
        prev_idx = STATE_ORDER.index(previous)
        cand_idx = STATE_ORDER.index(candidate)
        if cand_idx < prev_idx:
            required = int(cfg.get("state_hysteresis", {}).get("downgrade_days", 3))
            if persistence["improving"] < required:
                state = previous
                transition_note = f"降級需連續改善 {required} 天，目前僅 {persistence['improving']} 天"
        elif cand_idx > prev_idx:
            required = int(cfg.get("state_hysteresis", {}).get("upgrade_days", 2))
            if persistence["non_decreasing"] < required and cand_idx - prev_idx > 1:
                state = STATE_ORDER[min(prev_idx + 1, len(STATE_ORDER) - 1)]
                transition_note = f"升級採逐級遲滯，避免單日跳級"

    if pd.notna(momentum_5d) and momentum_5d >= 4:
        trend = "加速惡化"
    elif pd.notna(momentum_5d) and momentum_5d <= -4:
        trend = "持續改善"
    elif persistence["above_alert"] >= 3:
        trend = "高檔持平"
    else:
        trend = "震盪"

    velocity = _velocity_metrics(risk)
    reasons = _state_reasons(state, latest, breadth, persistence, cfg)
    accumulation_score = min(
        100.0,
        0.35 * float(percentile if pd.notna(percentile) else 0)
        + 0.25 * float(breadth.get("breadth_pct", 0))
        + 2.5 * min(persistence["above_observe"], 10)
        + 2.0 * min(max(velocity.get("daily_velocity_5d") or 0, 0), 5),
    )

    return {
        "state": state,
        "state_zh": STATE_ZH[state],
        "candidate_state": candidate,
        "candidate_state_zh": STATE_ZH[candidate],
        "previous_state": previous,
        "transition_note": transition_note,
        "risk_score": round(float(latest["risk_score"]), 1),
        "risk_percentile_180d": round(percentile, 1) if pd.notna(percentile) else None,
        "risk_rank_180d": rank,
        "history_count": int(len(valid_risk)),
        "accumulation_score": round(accumulation_score, 1),
        "momentum": {
            "1d": round(momentum_1d, 1) if pd.notna(momentum_1d) else None,
            "3d": round(momentum_3d, 1) if pd.notna(momentum_3d) else None,
            "5d": round(momentum_5d, 1) if pd.notna(momentum_5d) else None,
            "slope_5d": round(slope5, 2) if pd.notna(slope5) else None,
            "slope_10d": round(slope10, 2) if pd.notna(slope10) else None,
            "label": trend,
        },
        "velocity": velocity,
        "persistence": persistence,
        "breadth": breadth,
        "reasons": reasons,
        "recent_scores": [round(float(x), 1) for x in valid_risk.tail(10)],
    }


def apply_os_policy(decision: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    current_state = state.get("state", "NORMAL")
    persistence = state.get("persistence", {})
    confidence = float(decision.get("decision_confidence_pct", 0))
    mode = "452"
    action = "維持正常配置。"

    if current_state in {"LIQUIDITY_STRESS", "SYSTEMIC"} and persistence.get("above_risk_off", 0) >= 7 and confidence >= 70:
        mode = "433"
        action = "危機狀態已具持續性與廣度；進入 433 候選，仍套用 crisis_memory 防止單日反轉。"
    elif current_state in {"RISK_OFF", "CREDIT_STRESS", "LIQUIDITY_STRESS", "SYSTEMIC"} and persistence.get("above_alert", 0) >= 5 and confidence >= 65:
        mode = "514"
        action = "風險撤退已持續確認；切換至 514 候選，降低槓桿並提高短債。"
    elif current_state == "ROTATION":
        action = "維持 452；目前以板塊輪動為主，尚未形成廣泛避險。"

    out = dict(decision)
    out.update({
        "mode": mode,
        "state_policy_action": action,
        "market_state": current_state,
        "market_state_zh": state.get("state_zh"),
    })
    out["lamp"] = {"452": "🟢", "514": "🟡", "433": "🔴"}[mode]
    out["action"] = action
    return out
