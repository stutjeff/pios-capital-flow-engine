from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .config import load_yaml


def _read_snapshot(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    score = payload.get("risk_score", payload.get("score"))
    confidence = payload.get("confidence", payload.get("decision_confidence_pct", 0))
    try:
        score = float(score)
        confidence = float(confidence)
    except (TypeError, ValueError):
        return None
    return {"score": max(0.0, min(100.0, score)), "confidence": max(0.0, min(100.0, confidence)), "raw": payload}


def fuse(capital_flow_score: float, capital_flow_confidence: float, data_dir: Path) -> dict[str, Any]:
    cfg = load_yaml("state_engine.yaml").get("fusion", {})
    inputs = {
        "capital_flow": {"score": float(capital_flow_score), "confidence": float(capital_flow_confidence), "available": True},
        "macro": None,
        "news": None,
    }
    inputs["macro"] = _read_snapshot(data_dir / "external" / "macro_radar_latest.json")
    inputs["news"] = _read_snapshot(data_dir / "external" / "news_radar_latest.json")
    weights = {
        "capital_flow": float(cfg.get("capital_flow_weight", 0.5)),
        "macro": float(cfg.get("macro_weight", 0.3)),
        "news": float(cfg.get("news_weight", 0.2)),
    }
    numerator = 0.0
    denominator = 0.0
    available = []
    for key, item in inputs.items():
        if item is None:
            continue
        effective = weights[key] * max(0.25, item["confidence"] / 100.0)
        numerator += item["score"] * effective
        denominator += effective
        available.append(key)
    score = numerator / denominator if denominator else float(capital_flow_score)
    return {
        "fused_score": round(score, 1),
        "available_radars": available,
        "missing_radars": [x for x in ("macro", "news") if inputs[x] is None],
        "inputs": inputs,
        "is_full_fusion": len(available) == 3,
    }
