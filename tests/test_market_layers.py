import pandas as pd

from pios.core.scoring import analyze, build_contagion, build_time_layers, flow_map
from pios.core.state_engine import evaluate_state


def _timeseries():
    dates=pd.date_range('2026-01-01',periods=80)
    base=pd.Series(range(100,180),dtype=float)
    return pd.DataFrame({
        'date':dates.astype(str),
        'SOXX':base.tolist()[:-1]+[140.0],
        'SPY':base,
        'XLF_FINANCIALS':base*1.1,
        'TW_SEMICONDUCTOR':base.tolist()[:-1]+[145.0],
        'TW_LARGE_CAP':base.tolist()[:-1]+[160.0],
        'HY_OAS':pd.Series([3.0]*80),
        'IG_OAS':pd.Series([1.0]*80),
        'VIX':pd.Series([15.0]*80),
        'GLD':base,
        'TLT':base,
    })


def test_time_layers_are_separated():
    meta={
        'SOXX':{'market_session':'US_CLOSE','region':'US','data_type':'PRICE_PROXY'},
        'TW_SEMICONDUCTOR':{'market_session':'ASIA_CLOSE','region':'TAIWAN','data_type':'LOCAL_PRICE'},
    }
    a=analyze(_timeseries(),meta)
    layers=build_time_layers(a)
    assert 'us_previous_close' in layers['latest_session']
    assert 'asia_current_close' in layers['latest_session']


def test_flow_map_is_explicit_price_proxy():
    a=analyze(_timeseries())
    paths=flow_map(a)
    assert paths
    assert paths[0]['flow_type']=='PRICE_ROTATION_PROXY'
    assert paths[0]['true_flow_confirmed'] is False
    assert paths[0]['level'] in {'推測','初步確認','高度確認'}


def test_contagion_requires_sequential_confirmation():
    a=analyze(_timeseries())
    c=build_contagion(a)
    assert 0 <= c['stage'] <= 4
    if not c['asia_sector_followthrough']:
        assert c['stage'] <= 1


def test_aggressive_rotation_state():
    h=pd.DataFrame({
        'date':pd.date_range('2026-01-01',periods=6).astype(str),
        'risk_score':[15,16,17,18,19,20],
        'credit_score':[2]*6,'volatility_score':[2]*6,'dollar_rates_score':[2]*6,
        'risk_asset_score':[8]*6,'defensive_score':[1]*6,
    })
    state=evaluate_state(h,context={'contagion':{'stage':2,'label':'跨區域產業傳導'},'rotation_evidence':{'confirmed_paths':1}})
    assert state['state']=='AGGRESSIVE_ROTATION'
