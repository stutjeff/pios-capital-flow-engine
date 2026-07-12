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
        "version": 2,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
    }
    for event in events:
        start = date.fromisoformat(str(event["start"]))
        end = date.fromisoformat(str(event["end"]))
        print(f"Building analog {event['label']} {start}..{end}", flush=True)
        timeseries, _statuses = collect_range(start, end, model_only=True)
        risk_history = build_risk_history(timeseries, minimum_rows=25)
        if risk_history.empty:
            payload["events"].append({
                "id": event["id"], "label": event["label"], "start": str(start), "end": str(end),
                "status": "NO_DATA", "coverage_pct": 0,
            })
            continue

        profile = {
            column: round(float(pd.to_numeric(risk_history[column], errors="coerce").tail(20).mean()), 3)
            for column in COMPONENT_COLUMNS if column in risk_history
        }
        coverage = float(risk_history[COMPONENT_COLUMNS].notna().mean().mean() * 100)
        payload["events"].append({
            "id": event["id"],
            "label": event["label"],
            "start": str(start),
            "end": str(end),
            "status": "OK",
            "coverage_pct": round(coverage, 1),
            "dates": [str(x) for x in risk_history["date"].tolist()],
            "risk_trajectory": _numbers(risk_history["risk_score"]),
            "component_profile": profile,
            "component_series": {
                column: _numbers(risk_history[column]) for column in COMPONENT_COLUMNS
            },
        })

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
