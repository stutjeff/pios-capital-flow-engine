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


def build() -> None:
    events = load_yaml("historical_events.yaml").get("events", [])
    payload = {
        "version": 3,
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
