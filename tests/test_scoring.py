import pandas as pd
import numpy as np
from pios.core.scoring import analyze,decision,one_line_summary,flow_map


def sample():
    n=180
    dates=pd.date_range("2026-01-01",periods=n)
    return pd.DataFrame({"date":dates,"DXY_PROXY":np.linspace(100,105,n),"US_10Y_YIELD":np.linspace(4,4.5,n),"HY_OAS":np.linspace(3,3.2,n),"IG_OAS":np.linspace(1,1.1,n),"VIX":np.linspace(20,15,n),"SPY":np.linspace(500,510,n),"QQQ":np.linspace(500,480,n),"IWM":np.linspace(200,202,n),"SOXX":np.linspace(250,220,n),"GLD":np.linspace(200,190,n),"TLT":np.linspace(90,88,n),"EEM":np.linspace(45,42,n),"XLF_FINANCIALS":np.linspace(40,45,n),"XLE_ENERGY":np.linspace(80,85,n),"XLU_UTILITIES":np.linspace(65,67,n),"XLK_TECH":np.linspace(220,210,n),"FXI":np.linspace(25,26,n),"HYG":np.linspace(75,74,n),"LQD":np.linspace(105,104,n),"XLP_STAPLES":np.linspace(75,76,n)})


def test_analysis_and_decision():
    a=analyze(sample())
    d=decision(a)
    assert len(a)>10
    assert d["mode"] in {"452","514","433"}
    assert "switch_progress" in d
    assert set(d["switch_progress"])=={"514","433"}
    assert "strength_20d_pctile" in a.columns
    assert "event_duration_days" in a.columns
    assert "板塊輪動" in one_line_summary(a) or "全面避險" in one_line_summary(a)
    paths=flow_map(a)
    assert paths and {"from","to","spread_20d","stars"}.issubset(paths[0])
