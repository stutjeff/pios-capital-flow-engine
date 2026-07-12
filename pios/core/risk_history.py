from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from .scoring import analyze, decision

RISK_HISTORY_COLUMNS = [
    "date", "risk_score", "decision_confidence_pct", "data_completeness_pct",
    "signal_consistency_pct", "mode", "credit_score", "volatility_score",
    "dollar_rates_score", "risk_asset_score", "defensive_score",
]


def _component_map(d: dict) -> dict[str, float]:
    mapping = {c["name"]: float(c["score"]) for c in d.get("components", [])}
    return {
        "credit_score": mapping.get("信用市場", np.nan),
        "volatility_score": mapping.get("波動率", np.nan),
        "dollar_rates_score": mapping.get("美元與利率", np.nan),
        "risk_asset_score": mapping.get("風險資產撤退", np.nan),
        "defensive_score": mapping.get("避險與防禦輪動", np.nan),
    }


def build_risk_history(ts: pd.DataFrame, minimum_rows: int = 25) -> pd.DataFrame:
    if ts is None or ts.empty or "date" not in ts.columns:
        return pd.DataFrame(columns=RISK_HISTORY_COLUMNS)
    work = ts.copy().reset_index(drop=True)
    rows: list[dict] = []
    for end in range(minimum_rows, len(work) + 1):
        prefix = work.iloc[:end].copy()
        a = analyze(prefix)
        d = decision(a)
        rows.append({
            "date": str(prefix.iloc[-1]["date"]),
            "risk_score": d["risk_score"],
            "decision_confidence_pct": d["decision_confidence_pct"],
            "data_completeness_pct": d["data_completeness_pct"],
            "signal_consistency_pct": d["signal_consistency_pct"],
            "mode": d["mode"],
            **_component_map(d),
        })
    return pd.DataFrame(rows, columns=RISK_HISTORY_COLUMNS)


def merge_risk_history(current: pd.DataFrame, path: Path, keep_days: int = 180) -> pd.DataFrame:
    frames = [current]
    if path.exists():
        try:
            frames.insert(0, pd.read_csv(path))
        except Exception:
            pass
    out = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame(columns=RISK_HISTORY_COLUMNS)
    if out.empty:
        return pd.DataFrame(columns=RISK_HISTORY_COLUMNS)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    out = out.tail(keep_days)
    out["date"] = out["date"].dt.date.astype("string")
    return out.reset_index(drop=True)
