from __future__ import annotations
import argparse,json
from datetime import date,datetime
from pathlib import Path
import pandas as pd
from pios.core.config import load_yaml
from pios.core.engine import collect_range
from pios.core.risk_history import build_risk_history

OUT=Path("data/analog_library.json")

def build():
    events=load_yaml("historical_events.yaml").get("events",[])
    payload={"version":1,"built_at":datetime.utcnow().isoformat()+"Z","events":[]}
    for e in events:
        start=date.fromisoformat(str(e["start"])); end=date.fromisoformat(str(e["end"]))
        print(f"Building analog {e['label']} {start}..{end}",flush=True)
        ts,statuses=collect_range(start,end,model_only=True)
        rh=build_risk_history(ts,minimum_rows=25)
        if rh.empty:
            payload["events"].append({"id":e["id"],"label":e["label"],"start":str(start),"end":str(end),"status":"NO_DATA","coverage_pct":0})
            continue
        cols=["credit_score","volatility_score","dollar_rates_score","risk_asset_score","defensive_score"]
        profile={c:round(float(pd.to_numeric(rh[c],errors="coerce").tail(20).mean()),3) for c in cols if c in rh}
        coverage=float(rh[cols].notna().mean().mean()*100) if cols else 0
        payload["events"].append({"id":e["id"],"label":e["label"],"start":str(start),"end":str(end),"status":"OK","coverage_pct":round(coverage,1),"risk_trajectory":[round(float(x),2) for x in pd.to_numeric(rh["risk_score"],errors="coerce").dropna().tail(20)],"component_profile":profile})
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Saved {OUT}")

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--if-missing",action="store_true"); args=p.parse_args()
    if args.if_missing and OUT.exists(): print("Analog library already exists")
    else: build()
