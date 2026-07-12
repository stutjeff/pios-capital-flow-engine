from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from .config import load_yaml

VECTOR_COLS=["risk_score","credit_score","volatility_score","dollar_rates_score","risk_asset_score","defensive_score"]


def _normalize(x:np.ndarray)->np.ndarray:
    x=np.asarray(x,dtype=float)
    if len(x)==0:return x
    mean=np.nanmean(x); std=np.nanstd(x)
    return (x-mean)/std if std>1e-9 else x-mean


def _trajectory_similarity(current:pd.Series, reference:list[float])->float:
    a=pd.to_numeric(current,errors="coerce").dropna().values
    b=np.asarray(reference,dtype=float)
    n=min(len(a),len(b))
    if n<5:return float("nan")
    a=_normalize(a[-n:]); b=_normalize(b[-n:])
    rmse=float(np.sqrt(np.mean((a-b)**2)))
    return max(0.0,100.0*(1.0-rmse/3.0))


def _component_similarity(latest:pd.Series, profile:dict)->tuple[float,float]:
    common=[]
    for c in VECTOR_COLS[1:]:
        if c in profile and pd.notna(latest.get(c)):
            common.append((float(latest[c]),float(profile[c])))
    if not common:return float("nan"),0.0
    a=np.array([x[0] for x in common]); b=np.array([x[1] for x in common])
    denom=np.linalg.norm(a)*np.linalg.norm(b)
    cosine=float(np.dot(a,b)/denom) if denom else 0.0
    return max(0.0,min(100.0,(cosine+1)*50)),len(common)/(len(VECTOR_COLS)-1)*100


def compare(history:pd.DataFrame, library_path:Path)->dict[str,Any]:
    cfg=load_yaml("state_engine.yaml").get("historical_analogs",{})
    lookback=int(cfg.get("lookback_days",20)); mincov=float(cfg.get("minimum_coverage_pct",55)); topn=int(cfg.get("top_n",3))
    if not library_path.exists():
        return {"available":False,"reason":"analog library not built","matches":[]}
    try: library=json.loads(library_path.read_text(encoding="utf-8"))
    except Exception as exc:return {"available":False,"reason":f"invalid library: {exc}","matches":[]}
    if history.empty:return {"available":False,"reason":"risk history empty","matches":[]}
    latest=history.iloc[-1]
    matches=[]
    for event in library.get("events",[]):
        traj=_trajectory_similarity(history["risk_score"].tail(lookback),event.get("risk_trajectory",[]))
        comp,cov=_component_similarity(latest,event.get("component_profile",{}))
        if pd.isna(traj) and pd.isna(comp):continue
        score=(0 if pd.isna(traj) else traj)*0.6+(0 if pd.isna(comp) else comp)*0.4
        total_cov=min(100.0,(cov+float(event.get("coverage_pct",0)))/2)
        if total_cov<mincov:continue
        matches.append({"id":event.get("id"),"label":event.get("label"),"similarity_pct":round(score,1),"trajectory_pct":round(traj,1) if pd.notna(traj) else None,"component_pct":round(comp,1) if pd.notna(comp) else None,"coverage_pct":round(total_cov,1),"reference_start":event.get("start"),"reference_end":event.get("end")})
    matches.sort(key=lambda x:x["similarity_pct"],reverse=True)
    return {"available":bool(matches),"reason":"" if matches else "no match meets coverage","matches":matches[:topn],"built_at":library.get("built_at")}
