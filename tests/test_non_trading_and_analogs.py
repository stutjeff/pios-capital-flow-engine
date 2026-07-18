from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from pios.core.scoring import analyze, build_time_layers
from pios.core.analogs import compare


def test_returns_trim_to_actual_latest_date():
    dates=pd.date_range("2026-07-15",periods=4,freq="D")
    ts=pd.DataFrame({"date":dates.astype(str),"SPY":[100,95,95,95]})
    meta={"SPY":{"latest_date":"2026-07-16","market_session":"US_CLOSE","label":"美股大盤"}}
    a=analyze(ts,meta)
    value=float(a.loc[a.factor=="SPY","change_1d_pct"].iloc[0])
    assert round(value,1)==-5.0


def test_time_layer_has_session_note():
    ts=pd.DataFrame({"date":pd.date_range("2026-07-15",periods=3).astype(str),"SPY":[100,98,98]})
    a=analyze(ts,{"SPY":{"latest_date":"2026-07-16","market_session":"US_CLOSE","label":"美股大盤"}})
    layers=build_time_layers(a)
    assert "session_info" in layers
    assert layers["session_info"]["US_CLOSE"]["latest_market_date"]=="2026-07-16"


def test_trajectory_only_analog_is_accepted(tmp_path:Path):
    history=pd.DataFrame({
        "date":pd.date_range("2026-01-01",periods=20).astype(str),
        "risk_score":list(range(10,30)),
        "credit_score":[None]*20,"volatility_score":[None]*20,
        "dollar_rates_score":[None]*20,"risk_asset_score":[None]*20,"defensive_score":[None]*20,
    })
    payload={"version":3,"events":[{
        "id":"x","label":"事件","status":"PARTIAL","coverage_pct":0,
        "dates":pd.date_range("2000-01-01",periods=30).astype(str).tolist(),
        "risk_trajectory":list(range(0,30)),"component_series":{},"component_profile":{},
    }]}
    path=tmp_path/"analog.json"
    path.write_text(json.dumps(payload),encoding="utf-8")
    result=compare(history,path)
    assert result["available"]
    assert result["matches"][0]["comparison_mode"]=="TRAJECTORY_ONLY"
