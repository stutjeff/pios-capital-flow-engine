from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .config import load_yaml
from .history import merge_rolling
from .models import ProviderStatus,status,statuses_to_frame,now_taipei
from .scoring import analyze,decision
from .report import telegram_message
from .telegram import send
from pios.providers.base import ProviderContext
from pios.providers.registry import discover,create

VERSION='5.3.2'
DATA=Path('data'); TS=DATA/'capital_flow_timeseries_180d.csv'; STATUS=DATA/'source_status.csv'; ANALYSIS=DATA/'factor_analysis.csv'; DECISION=DATA/'decision.json'; RUNLOG=DATA/'run_log.txt'
TAIPEI=timezone(timedelta(hours=8))

def log(msg):
    DATA.mkdir(parents=True,exist_ok=True); print(msg,flush=True)
    with RUNLOG.open('a',encoding='utf-8') as f:f.write(str(msg)+'\n')

def _instances():
    cfg=load_yaml('providers.yaml'); items=list(cfg.get('providers',[]))
    sectors=load_yaml('sectors.yaml').get('market_symbols',{})
    for symbol,column in sectors.items():items.append({'id':f'market_{symbol.lower()}','type':'market_chain','symbol':symbol,'column':column,'used_in_model':True})
    return [x for x in items if x.get('enabled',True)]

def collect():
    discover(); today=datetime.now(TAIPEI).date(); ctx=ProviderContext(today=today,start=today-timedelta(days=300),config={})
    frames=[]; statuses=[]; instances=_instances()
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs={pool.submit(create(x).fetch,ctx):x['id'] for x in instances}
        for fut in as_completed(futs):
            name=futs[fut]
            try:
                df,ss=fut.result(); frames.append(df); statuses.extend(ss)
            except Exception as exc:statuses.append(status(name,'RUNTIME','EXCEPTION',error_type=type(exc).__name__,detail=repr(exc)))
    window=int(load_yaml('scoring.yaml').get('window_days',180))
    ts=merge_rolling(frames,TS,today,window)
    if 'TLT' in ts:
        ret=pd.to_numeric(ts['TLT'],errors='coerce').pct_change(); ts['MOVE_PROXY']=(ret.rolling(20,min_periods=10).std()*np.sqrt(252)*100).round(4)
        statuses.append(status('Derived:TLT_20D_VOL','DERIVED_FACTOR','OK',adapter_state='DERIVED',history_supported='YES',history_rows=int(ts['MOVE_PROXY'].notna().sum()),latest_date=str(ts.loc[ts['MOVE_PROXY'].notna(),'date'].max()) if ts['MOVE_PROXY'].notna().any() else '',endpoint='local calculation',fmt='20D std(TLT returns)*sqrt(252)*100',detail='MOVE proxy, not proprietary MOVE index'))
    return ts,statuses

def run():
    DATA.mkdir(exist_ok=True); RUNLOG.write_text('',encoding='utf-8'); log(f'PIOS Capital Flow Engine V{VERSION}')
    ts,statuses=collect(); a=analyze(ts); d=decision(a); d.update({'version':VERSION,'generated_at_taipei':now_taipei()})
    ts.to_csv(TS,index=False); statuses_to_frame(statuses).to_csv(STATUS,index=False); a.to_csv(ANALYSIS,index=False); DECISION.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    text=telegram_message(VERSION,d['generated_at_taipei'],d,a,statuses,len(ts)); ok,detail=send(text); log(f'Telegram: {detail}')
    if not ok and detail!='MISSING_TELEGRAM_SECRET':raise RuntimeError(f'Telegram failed: {detail}')
    return d
