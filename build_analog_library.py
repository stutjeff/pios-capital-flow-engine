from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from pios.core.config import load_yaml
from pios.core.engine import collect_range
from pios.core.risk_history import build_risk_history

OUT = Path("data/analog_library.json")
COMPONENT_COLUMNS = ["credit_score", "volatility_score", "dollar_rates_score", "risk_asset_score", "defensive_score"]


def _numbers(series: pd.Series) -> list[float | None]:
    out: list[float | None] = []
    for value in pd.to_numeric(series, errors="coerce"):
        out.append(None if pd.isna(value) else round(float(value), 3))
    return out




def _macro_fallback_history(timeseries: pd.DataFrame, minimum_rows: int = 20) -> pd.DataFrame:
    """Build a conservative historical trajectory from official macro series.

    Old event windows may not be available from current equity API plans. Rather than
    producing an empty library, use the official FRED factors that are actually
    returned. Missing equity/defensive components remain null and comparison is
    explicitly marked macro-only.
    """
    if timeseries is None or timeseries.empty or "date" not in timeseries:
        return pd.DataFrame()
    work=timeseries.copy()
    work["date"]=pd.to_datetime(work["date"],errors="coerce")
    work=work.dropna(subset=["date"]).sort_values("date")
    factors=["HY_OAS","IG_OAS","VIX","DXY_PROXY","US_10Y_YIELD"]
    if sum(c in work and work[c].notna().sum()>=minimum_rows for c in factors)<3:
        return pd.DataFrame()
    out=pd.DataFrame({"date":work["date"].dt.date.astype("string")})
    def ret20(col):
        x=pd.to_numeric(work.get(col),errors="coerce")
        return x.pct_change(20,fill_method=None)*100
    hy=ret20("HY_OAS") if "HY_OAS" in work else pd.Series(index=work.index,dtype=float)
    ig=ret20("IG_OAS") if "IG_OAS" in work else pd.Series(index=work.index,dtype=float)
    dxy=ret20("DXY_PROXY") if "DXY_PROXY" in work else pd.Series(index=work.index,dtype=float)
    y10=ret20("US_10Y_YIELD") if "US_10Y_YIELD" in work else pd.Series(index=work.index,dtype=float)
    vix=pd.to_numeric(work.get("VIX"),errors="coerce") if "VIX" in work else pd.Series(index=work.index,dtype=float)
    vix_pct=vix.rolling(180,min_periods=20).apply(lambda x: float((x<=x[-1]).mean()*100),raw=True)
    credit=(hy.clip(lower=0).fillna(0)*1.5 + ig.clip(lower=0).fillna(0)*1.5).clip(0,20)
    volatility=(vix_pct.fillna(0)*0.15).clip(0,15)
    dollar_rates=(dxy.clip(lower=0).fillna(0)*2 + y10.clip(lower=0).fillna(0)).clip(0,20)
    out["credit_score"]=credit
    out["volatility_score"]=volatility
    out["dollar_rates_score"]=dollar_rates
    out["risk_asset_score"]=float("nan")
    out["defensive_score"]=float("nan")
    out["risk_score"]=(credit+volatility+dollar_rates).clip(0,55)
    out["decision_confidence_pct"]=60.0
    out["data_completeness_pct"]=60.0
    out["signal_consistency_pct"]=60.0
    out["mode"]="HISTORICAL_MACRO_ONLY"
    return out[out["risk_score"].notna()].reset_index(drop=True)

def build() -> None:
    events = load_yaml("historical_events.yaml").get("events", [])
    payload = {
        "version": 4,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
    }
    for event in events:
        start = date.fromisoformat(str(event["start"]))
        end = date.fromisoformat(str(event["end"]))
        print(f"Building analog {event['label']} {start}..{end}", flush=True)
        timeseries, _statuses = collect_range(start, end, model_only=True)
        available_rows=int(timeseries.drop(columns=["date"],errors="ignore").notna().any(axis=1).sum()) if not timeseries.empty else 0
        minimum_rows=max(10,min(25,max(10,available_rows//3)))
        risk_history = build_risk_history(timeseries, minimum_rows=minimum_rows)
        build_mode="FULL_MODEL"
        if risk_history.empty or pd.to_numeric(risk_history.get("risk_score"),errors="coerce").notna().sum()<5:
            risk_history=_macro_fallback_history(timeseries, minimum_rows=max(10,minimum_rows//2))
            build_mode="MACRO_FALLBACK"
        if risk_history.empty:
            available_columns=[c for c in timeseries.columns if c!="date" and timeseries[c].notna().any()] if not timeseries.empty else []
            payload["events"].append({
                "id": event["id"], "label": event["label"], "start": str(start), "end": str(end),
                "status": "NO_DATA", "coverage_pct": 0, "available_rows":available_rows,
                "available_columns":available_columns,
                "reason":"Historical providers did not return enough model rows",
            })
            continue

        profile = {
            column: round(float(pd.to_numeric(risk_history[column], errors="coerce").tail(20).mean()), 3)
            for column in COMPONENT_COLUMNS if column in risk_history
        }
        present_components=[c for c in COMPONENT_COLUMNS if c in risk_history.columns]
        coverage = float(risk_history[present_components].notna().mean().mean() * 100) if present_components else 0.0
        event_status="OK" if coverage>=55 else "PARTIAL"
        payload["events"].append({
            "id": event["id"],
            "label": event["label"],
            "start": str(start),
            "end": str(end),
            "status": event_status,
            "build_mode": build_mode,
            "coverage_pct": round(coverage, 1),
            "available_rows":available_rows,
            "risk_rows":len(risk_history),
            "dates": [str(x) for x in risk_history["date"].tolist()],
            "risk_trajectory": _numbers(risk_history["risk_score"]),
            "component_profile": profile,
            "component_series": {
                column: _numbers(risk_history[column]) for column in COMPONENT_COLUMNS
            },
        })

    payload["summary"]={
        "total_events":len(payload["events"]),
        "usable_events":sum(1 for e in payload["events"] if len(e.get("risk_trajectory",[]) or [])>=5),
        "status_counts":{},
    }
    for e in payload["events"]:
        key=e.get("status","UNKNOWN")
        payload["summary"]["status_counts"][key]=payload["summary"]["status_counts"].get(key,0)+1
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--if-missing", action="store_true")
    args = parser.parse_args()
    if args.if_missing and OUT.exists():
        print("Analog library already exists")
    else:
        build()
