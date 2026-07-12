from __future__ import annotations
from datetime import date,timedelta
from pathlib import Path
import pandas as pd

def merge_rolling(frames:list[pd.DataFrame], history_path:Path, today:date, window_days:int=180)->pd.DataFrame:
    merged=None
    for df in frames:
        if df is None or df.empty: continue
        merged=df.copy() if merged is None else merged.merge(df,on='date',how='outer')
    if merged is None: merged=pd.DataFrame({'date':[]})
    merged['date']=pd.to_datetime(merged['date'],errors='coerce')
    merged=merged.dropna(subset=['date']).sort_values('date').drop_duplicates('date',keep='last')
    if history_path.exists():
        old=pd.read_csv(history_path); old['date']=pd.to_datetime(old['date'],errors='coerce')
        merged=pd.concat([old,merged],ignore_index=True,sort=False).sort_values('date').drop_duplicates('date',keep='last')
    cal=pd.DataFrame({'date':pd.date_range(pd.Timestamp(today-timedelta(days=window_days-1)),pd.Timestamp(today),freq='D')})
    merged=cal.merge(merged,on='date',how='left').sort_values('date')
    cols=[c for c in merged.columns if c!='date']
    if cols: merged[cols]=merged[cols].ffill(limit=7)
    merged['date']=merged['date'].dt.date.astype('string')
    return merged.tail(window_days).reset_index(drop=True)
