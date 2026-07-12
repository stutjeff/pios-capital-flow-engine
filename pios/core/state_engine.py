from __future__ import annotations
from dataclasses import dataclass
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
    columns = ["credit_score", "volatility_score", "dollar_rates_score", "risk_asset_score", "defensive_score"]
    maxima = {"credit_score":20, "volatility_score":15, "dollar_rates_score":20, "risk_asset_score":25, "defensive_score":20}
    active=[]
    for c in columns:
        v=float(latest.get(c,0) or 0)
        ratio=v/maxima[c]
        if ratio>=0.35: active.append(c)
    pct=len(active)/len(columns)*100
    return {"active_modules":active,"active_count":len(active),"total_modules":len(columns),"breadth_pct":round(pct,1)}


def _state_candidate(latest: pd.Series, history: pd.DataFrame, breadth: dict, cfg: dict) -> str:
    risk=float(latest.get("risk_score",0)); b=breadth["breadth_pct"]
    credit=float(latest.get("credit_score",0)); vol=float(latest.get("volatility_score",0)); defensive=float(latest.get("defensive_score",0))
    t=cfg.get("risk_thresholds",{})
    if risk>=float(t.get("systemic",75)) and b>=75: return "SYSTEMIC"
    if risk>=float(t.get("liquidity_stress",60)) and b>=60 and vol>=8 and defensive>=7: return "LIQUIDITY_STRESS"
    if risk>=float(t.get("credit_stress",48)) and credit>=12: return "CREDIT_STRESS"
    if risk>=float(t.get("risk_off",35)) and b>=float(cfg.get("breadth",{}).get("risk_off_pct",57)): return "RISK_OFF"
    risk_asset=float(latest.get("risk_asset_score",0))
    if risk_asset>=7 or (risk>=float(t.get("observe",15)) and b<57): return "ROTATION"
    return "NORMAL"


def evaluate_state(history: pd.DataFrame, previous_state: str | None = None) -> dict[str, Any]:
    cfg=load_yaml("state_engine.yaml")
    if history is None or history.empty:
        return {"state":"NORMAL","state_zh":STATE_ZH["NORMAL"],"reason":"風險歷史不足"}
    h=history.copy()
    for c in h.columns:
        if c!="date" and c!="mode": h[c]=pd.to_numeric(h[c],errors="coerce")
    latest=h.iloc[-1]
    breadth=_breadth(latest)
    candidate=_state_candidate(latest,h,breadth,cfg)
    risk=h["risk_score"]
    momentum_1d=float(risk.iloc[-1]-risk.iloc[-2]) if len(risk)>=2 else float("nan")
    momentum_3d=float(risk.iloc[-1]-risk.iloc[-4]) if len(risk)>=4 else float("nan")
    momentum_5d=float(risk.iloc[-1]-risk.iloc[-6]) if len(risk)>=6 else float("nan")
    slope5=_slope(risk,5); slope10=_slope(risk,10)
    thresholds=cfg.get("risk_thresholds",{})
    persistence={
        "above_observe":_streak(risk,lambda x:x>=float(thresholds.get("observe",15))),
        "above_alert":_streak(risk,lambda x:x>=float(thresholds.get("alert",25))),
        "above_risk_off":_streak(risk,lambda x:x>=float(thresholds.get("risk_off",35))),
        "non_decreasing":_streak(risk.diff().fillna(0),lambda x:x>=-0.25),
        "improving":_streak(risk.diff().fillna(0),lambda x:x<0),
    }
    percentile=float((risk.dropna()<=risk.dropna().iloc[-1]).mean()*100) if risk.notna().sum()>=20 else float("nan")
    rank=int((risk.dropna()>risk.dropna().iloc[-1]).sum()+1) if risk.notna().sum() else 0
    previous=previous_state if previous_state in STATE_ORDER else None
    state=candidate
    if previous:
        prev_idx=STATE_ORDER.index(previous); cand_idx=STATE_ORDER.index(candidate)
        if cand_idx<prev_idx:
            required=int(cfg.get("state_hysteresis",{}).get("downgrade_days",3))
            if persistence["improving"]<required: state=previous
        elif cand_idx>prev_idx:
            required=int(cfg.get("state_hysteresis",{}).get("upgrade_days",2))
            if persistence["non_decreasing"]<required and cand_idx-prev_idx>1: state=STATE_ORDER[min(prev_idx+1,len(STATE_ORDER)-1)]
    trend="加速惡化" if pd.notna(momentum_5d) and momentum_5d>=4 else "持續改善" if pd.notna(momentum_5d) and momentum_5d<=-4 else "高檔持平" if persistence["above_alert"]>=3 else "震盪"
    return {
        "state":state,"state_zh":STATE_ZH[state],"candidate_state":candidate,"candidate_state_zh":STATE_ZH[candidate],
        "risk_score":round(float(latest["risk_score"]),1),"risk_percentile_180d":round(percentile,1) if pd.notna(percentile) else None,
        "risk_rank_180d":rank,"history_count":int(risk.notna().sum()),
        "momentum":{"1d":round(momentum_1d,1) if pd.notna(momentum_1d) else None,"3d":round(momentum_3d,1) if pd.notna(momentum_3d) else None,"5d":round(momentum_5d,1) if pd.notna(momentum_5d) else None,"slope_5d":round(slope5,2) if pd.notna(slope5) else None,"slope_10d":round(slope10,2) if pd.notna(slope10) else None,"label":trend},
        "persistence":persistence,"breadth":breadth,
        "recent_scores":[round(float(x),1) for x in risk.dropna().tail(10)],
    }


def apply_os_policy(decision: dict[str,Any], state: dict[str,Any]) -> dict[str,Any]:
    s=state.get("state","NORMAL"); p=state.get("persistence",{}); confidence=float(decision.get("decision_confidence_pct",0))
    mode="452"; action="維持正常配置。"
    if s in {"LIQUIDITY_STRESS","SYSTEMIC"} and p.get("above_risk_off",0)>=7 and confidence>=70:
        mode="433"; action="危機狀態已具持續性與廣度；進入 433 候選，仍套用 crisis_memory 防止單日反轉。"
    elif s in {"RISK_OFF","CREDIT_STRESS","LIQUIDITY_STRESS","SYSTEMIC"} and p.get("above_alert",0)>=5 and confidence>=65:
        mode="514"; action="風險撤退已持續確認；切換至 514 候選，降低槓桿並提高短債。"
    elif s=="ROTATION":
        action="維持 452；目前以板塊輪動為主，尚未形成廣泛避險。"
    decision=dict(decision)
    decision.update({"mode":mode,"state_policy_action":action,"market_state":s,"market_state_zh":state.get("state_zh")})
    decision["lamp"]={"452":"🟢","514":"🟡","433":"🔴"}[mode]
    decision["action"]=action
    return decision
