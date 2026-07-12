from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pios.core.analogs import compare
from pios.core.state_engine import evaluate_state


def _history(scores):
    rows=[]
    for i, score in enumerate(scores):
        rows.append({
            'date': f'2026-01-{i+1:02d}',
            'risk_score': score,
            'credit_score': score*0.18,
            'volatility_score': score*0.12,
            'dollar_rates_score': score*0.10,
            'risk_asset_score': score*0.30,
            'defensive_score': score*0.10,
        })
    return pd.DataFrame(rows)


def test_velocity_and_reasons_present():
    state=evaluate_state(_history([8,10,12,14,16,18,20,22,24,26]))
    assert state['velocity']['daily_velocity_5d'] > 0
    assert state['persistence']['above_observe'] >= 6
    assert 'summary' in state['reasons']
    assert state['accumulation_score'] > 0


def test_analog_phase_and_next_stage(tmp_path: Path):
    event_scores=[5,6,7,8,9,10,12,14,16,18,20,23,26,30,35,40,45,48,50,52,54,56,58,60,62,64,66,68,70,72]
    payload={
        'version':2,
        'built_at':'2026-01-01T00:00:00Z',
        'events':[{
            'id':'test','label':'測試危機','start':'2000-01-01','end':'2000-02-01','coverage_pct':100,
            'dates':[f'2000-01-{i+1:02d}' for i in range(len(event_scores))],
            'risk_trajectory':event_scores,
            'component_profile':{'credit_score':10,'volatility_score':8,'dollar_rates_score':7,'risk_asset_score':12,'defensive_score':6},
            'component_series':{
                'credit_score':[x*0.18 for x in event_scores],
                'volatility_score':[x*0.12 for x in event_scores],
                'dollar_rates_score':[x*0.10 for x in event_scores],
                'risk_asset_score':[x*0.30 for x in event_scores],
                'defensive_score':[x*0.10 for x in event_scores],
            },
        }],
    }
    path=tmp_path/'analogs.json'
    path.write_text(json.dumps(payload),encoding='utf-8')
    result=compare(_history(event_scores[5:25]),path)
    assert result['available']
    match=result['matches'][0]
    assert match['phase_day'] is not None
    assert 'next_stage' in match
    assert match['next_stage']['available']
