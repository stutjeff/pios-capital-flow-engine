import pandas as pd
from pios.core.risk_history import build_risk_history


def test_risk_history_builds():
    n=40
    df=pd.DataFrame({
        "date":pd.date_range("2026-01-01",periods=n).astype(str),
        "DXY_PROXY":range(100,100+n),"US_10Y_YIELD":[4+i*.01 for i in range(n)],
        "HY_OAS":[3+i*.01 for i in range(n)],"IG_OAS":[1+i*.005 for i in range(n)],
        "VIX":[15+i*.1 for i in range(n)],"SPY":range(500,500+n),"QQQ":range(400,400+n),
        "IWM":range(200,200+n),"SOXX":range(600,600+n),"GLD":range(180,180+n),
        "TLT":range(90,90+n),"EEM":range(40,40+n),"XLF_FINANCIALS":range(35,35+n),
    })
    out=build_risk_history(df,minimum_rows=25)
    assert len(out)==16
    assert "risk_score" in out
