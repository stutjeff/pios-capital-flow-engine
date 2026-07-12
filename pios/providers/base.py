from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
import pandas as pd
from pios.core.http import env
from pios.core.models import ProviderStatus, status

@dataclass
class ProviderContext:
    today: date
    start: date
    config: dict[str,Any]

class Provider(ABC):
    provider_type='base'
    def __init__(self, instance: dict[str,Any]): self.instance=instance
    @abstractmethod
    def fetch(self, ctx: ProviderContext) -> tuple[pd.DataFrame,list[ProviderStatus]]: ...


def frame(rows, column):
    if not rows:return pd.DataFrame(columns=['date',column])
    df=pd.DataFrame(rows)
    if 'date' not in df or column not in df:return pd.DataFrame(columns=['date',column])
    df['date']=pd.to_datetime(df['date'],errors='coerce').dt.date.astype('string')
    df[column]=pd.to_numeric(df[column],errors='coerce')
    return df.dropna(subset=['date',column]).drop_duplicates('date',keep='last').sort_values('date')

def result_status(source,category,df,**kw):
    latest=str(df['date'].max()) if not df.empty else ''
    return status(source,category,'OK' if not df.empty else 'NO_DATA',history_rows=len(df),latest_date=latest,detail='data received' if not df.empty else 'no usable rows',**kw)

def missing(source,category,secret,endpoint,fmt,history='NO',used=False):
    return pd.DataFrame(), [status(source,category,'MISSING_KEY',error_type='MISSING_KEY',requires_key=True,secret_name=secret,history_supported=history,used_in_model=used,endpoint=endpoint,fmt=fmt,detail=f'GitHub Secret {secret} is missing.')]
