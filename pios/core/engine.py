from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .config import load_yaml
from .history import merge_rolling
from .models import status,statuses_to_frame,now_taipei
from .scoring import analyze,decision
from .risk_history import build_risk_history,merge_risk_history
from .state_engine import evaluate_state,apply_os_policy
from .analogs import compare as compare_analogs
from .fusion import fuse
from .report import telegram_message
from .telegram import send
from pios.providers.base import ProviderContext
from pios.providers.registry import discover,create

VERSION='6.0.0'
DATA=Path('data')
TS=DATA/'capital_flow_timeseries_180d.csv'
STATUS=DATA/'source_status.csv'
ANALYSIS=DATA/'factor_analysis.csv'
DECISION=DATA/'decision.json'
RISK_HISTORY=DATA/'risk_state_history_180d.csv'
STATE_HISTORY=DATA/'market_state_history_180d.csv'
ANALOG_LIBRARY=DATA/'analog_library.json'
RUNLOG=DATA/'run_log.txt'
TAIPEI=timezone(timedelta(hours=8))


def log(msg):
    DATA.mkdir(parents=True,exist_ok=True); print(msg,flush=True)
    with RUNLOG.open('a',encoding='utf-8') as f:f.write(str(msg)+'\n')


def _instances(model_only:bool=False):
    cfg=load_yaml('providers.yaml'); items=list(cfg.get('providers',[]))
    sectors=load_yaml('sectors.yaml').get('market_symbols',{})
    for symbol,column in sectors.items():items.append({'id':f'market_{symbol.lower()}','type':'market_chain','symbol':symbol,'column':column,'used_in_model':True})
    enabled=[x for x in items if x.get('enabled',True)]
    return [x for x in enabled if x.get('used_in_model',False)] if model_only else enabled


def _collect_instances(instances,ctx:ProviderContext):
    frames=[]; statuses=[]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs={pool.submit(create(x).fetch,ctx):x['id'] for x in instances}
        for fut in as_completed(futs):
            name=futs[fut]
            try:
                df,ss=fut.result(); frames.append(df); statuses.extend(ss)
            except Exception as exc:
                statuses.append(status(name,'RUNTIME','EXCEPTION',error_type=type(exc).__name__,detail=repr(exc)))
    return frames,statuses


def _merge_range(frames:list[pd.DataFrame],start:date,end:date)->pd.DataFrame:
    merged=None
    for df in frames:
        if df is None or df.empty:continue
        merged=df.copy() if merged is None else merged.merge(df,on='date',how='outer')
    if merged is None:return pd.DataFrame({'date':[]})
    merged['date']=pd.to_datetime(merged['date'],errors='coerce')
    merged=merged.dropna(subset=['date']).sort_values('date').drop_duplicates('date',keep='last')
    cal=pd.DataFrame({'date':pd.date_range(pd.Timestamp(start),pd.Timestamp(end),freq='D')})
    merged=cal.merge(merged,on='date',how='left').sort_values('date')
    cols=[c for c in merged.columns if c!='date']
    if cols:merged[cols]=merged[cols].ffill(limit=7)
    merged['date']=merged['date'].dt.date.astype('string')
    return merged.reset_index(drop=True)


def _derive(ts:pd.DataFrame,statuses:list):
    if 'TLT' in ts:
        ret=pd.to_numeric(ts['TLT'],errors='coerce').pct_change(fill_method=None)
        ts['MOVE_PROXY']=(ret.rolling(20,min_periods=10).std()*np.sqrt(252)*100).round(4)
        statuses.append(status('Derived:TLT_20D_VOL','DERIVED_FACTOR','OK',adapter_state='DERIVED',history_supported='YES',history_rows=int(ts['MOVE_PROXY'].notna().sum()),latest_date=str(ts.loc[ts['MOVE_PROXY'].notna(),'date'].max()) if ts['MOVE_PROXY'].notna().any() else '',endpoint='local calculation',fmt='20D std(TLT returns)*sqrt(252)*100',detail='MOVE proxy, not proprietary MOVE index'))
    return ts,statuses


def collect_range(start:date,end:date,model_only:bool=False):
    discover(); ctx=ProviderContext(today=end,start=start,config={})
    frames,statuses=_collect_instances(_instances(model_only=model_only),ctx)
    ts=_merge_range(frames,start,end)
    return _derive(ts,statuses)


def collect():
    today=datetime.now(TAIPEI).date()
    ctx=ProviderContext(today=today,start=today-timedelta(days=300),config={})
    discover(); frames,statuses=_collect_instances(_instances(),ctx)
    window=int(load_yaml('scoring.yaml').get('window_days',180))
    ts=merge_rolling(frames,TS,today,window)
    return _derive(ts,statuses)


def _previous_state()->str|None:
    if not DECISION.exists():return None
    try:return json.loads(DECISION.read_text(encoding='utf-8')).get('market_state')
    except Exception:return None


def _append_state_history(state_data:dict,generated_at:str)->pd.DataFrame:
    row={
        'date':generated_at[:10],
        'state':state_data.get('state'),
        'state_zh':state_data.get('state_zh'),
        'risk_score':state_data.get('risk_score'),
        'risk_percentile_180d':state_data.get('risk_percentile_180d'),
        'breadth_pct':state_data.get('breadth',{}).get('breadth_pct'),
        'momentum_5d':state_data.get('momentum',{}).get('5d'),
        'persistence_alert':state_data.get('persistence',{}).get('above_alert'),
    }
    new=pd.DataFrame([row])
    if STATE_HISTORY.exists():
        try:new=pd.concat([pd.read_csv(STATE_HISTORY),new],ignore_index=True,sort=False)
        except Exception:pass
    new['date']=pd.to_datetime(new['date'],errors='coerce')
    new=new.dropna(subset=['date']).sort_values('date').drop_duplicates('date',keep='last').tail(180)
    new['date']=new['date'].dt.date.astype('string')
    return new.reset_index(drop=True)


def run():
    DATA.mkdir(exist_ok=True); (DATA/'external').mkdir(exist_ok=True)
    RUNLOG.write_text('',encoding='utf-8'); log(f'PIOS Market State Engine V{VERSION}')
    ts,statuses=collect(); log(f'Collected timeseries rows={len(ts)}')
    a=analyze(ts); base=decision(a)
    generated=now_taipei()
    current_risk=build_risk_history(ts)
    rh=merge_risk_history(current_risk,RISK_HISTORY,180)
    state_data=evaluate_state(rh,_previous_state())
    d=apply_os_policy(base,state_data)
    analogs=compare_analogs(rh,ANALOG_LIBRARY)
    fusion=fuse(d['risk_score'],d['decision_confidence_pct'],DATA)
    d.update({'version':VERSION,'generated_at_taipei':generated,'state_engine':state_data,'historical_analogs':analogs,'radar_fusion':fusion})
    sh=_append_state_history(state_data,generated)
    ts.to_csv(TS,index=False)
    statuses_to_frame(statuses).to_csv(STATUS,index=False)
    a.to_csv(ANALYSIS,index=False)
    rh.to_csv(RISK_HISTORY,index=False)
    sh.to_csv(STATE_HISTORY,index=False)
    DECISION.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    text=telegram_message(VERSION,generated,d,a,statuses,len(ts),rh)
    ok,detail=send(text); log(f'Telegram: {detail}')
    if not ok and detail!='MISSING_TELEGRAM_SECRET':raise RuntimeError(f'Telegram failed: {detail}')
    return d
