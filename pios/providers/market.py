from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pandas as pd
from .base import Provider,ProviderContext
from .registry import register
from pios.core.config import load_yaml
from .market_backends import discover_backends,get_backend

TAIPEI=timezone(timedelta(hours=8))

@register('market_chain')
class MarketChainProvider(Provider):
    def fetch(self,ctx:ProviderContext):
        discover_backends()
        symbol=str(self.instance['symbol'])
        column=self.instance['column']
        used=bool(self.instance.get('used_in_model',True))
        exchange=str(self.instance.get('exchange','US'))
        statuses=[]
        order=load_yaml('market_backends.yaml').get('order',['eodhd','fmp','alphavantage'])
        for name in order:
            df,s=get_backend(name).fetch(symbol,column,ctx,used,exchange)
            s.market_session=str(self.instance.get('session',''))
            s.region=str(self.instance.get('region',''))
            s.data_type=str(self.instance.get('data_type','PRICE_PROXY'))
            s.market_date=s.latest_date
            if s.latest_date:
                try:
                    latest=pd.Timestamp(s.latest_date)
                    now=pd.Timestamp(datetime.now(TAIPEI))
                    s.data_lag_hours=str(round(max(0,(now.tz_localize(None)-latest).total_seconds()/3600),1))
                except Exception:
                    s.data_lag_hours=''
            statuses.append(s)
            if not df.empty:return df,statuses
        return pd.DataFrame(),statuses
