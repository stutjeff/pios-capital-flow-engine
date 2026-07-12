import pandas as pd
from pios.core.state_engine import evaluate_state,apply_os_policy


def sample(scores):
    return pd.DataFrame({
        "date":pd.date_range("2026-01-01",periods=len(scores)).astype(str),
        "risk_score":scores,
        "credit_score":[2]*len(scores),
        "volatility_score":[2]*len(scores),
        "dollar_rates_score":[2]*len(scores),
        "risk_asset_score":[8]*len(scores),
        "defensive_score":[1]*len(scores),
    })


def test_rotation_and_persistence():
    s=evaluate_state(sample([10,12,14,16,18,20]))
    assert s["state"]=="ROTATION"
    assert s["persistence"]["above_observe"]==3
    assert s["momentum"]["5d"]==10.0


def test_os_policy_requires_persistence():
    d={"decision_confidence_pct":80,"lamp":"🟢","mode":"452"}
    state={"state":"RISK_OFF","state_zh":"風險撤退","persistence":{"above_alert":5,"above_risk_off":0}}
    out=apply_os_policy(d,state)
    assert out["mode"]=="514"
