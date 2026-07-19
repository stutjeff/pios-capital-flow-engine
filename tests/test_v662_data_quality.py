import pandas as pd
from pios.core.scoring import analyze, decision, build_contagion


def test_market_calendar_fill_does_not_create_fake_zero_returns():
    dates=pd.date_range('2026-07-01', periods=12, freq='D')
    values=[100,101,102,102,102,103,104,105,105,105,106,107]
    ts=pd.DataFrame({'date':dates.astype(str),'SPY':values})
    meta={'SPY':{'latest_date':'2026-07-12','market_session':'US_CLOSE','label':'美股大盤'}}
    a=analyze(ts,meta)
    row=a.loc[a.factor=='SPY'].iloc[0]
    assert pd.notna(row.change_5d_pct)
    assert row.change_5d_pct != 0


def test_confidence_cannot_exceed_completeness():
    ts=pd.DataFrame({'date':pd.date_range('2026-01-01',periods=40).astype(str),'VIX':range(40)})
    d=decision(analyze(ts))
    assert d['decision_confidence_pct'] <= d['data_completeness_pct']


def test_contagion_marks_unassessable_when_asia_missing():
    ts=pd.DataFrame({'date':pd.date_range('2026-01-01',periods=40).astype(str),'SOXX':[100-i for i in range(40)]})
    c=build_contagion(analyze(ts))
    assert c['assessable'] is False
    assert c['label']=='資料不足，暫不可判定'
