from __future__ import annotations
import pandas as pd
from .base import Provider,ProviderContext
from .registry import register
from pios.core.config import load_yaml
from .market_backends import discover_backends,get_backend

@register('market_chain')
class MarketChainProvider(Provider):
    def fetch(self,ctx:ProviderContext):
        discover_backends()
        symbol=self.instance['symbol'];column=self.instance['column'];used=bool(self.instance.get('used_in_model',True));statuses=[]
        order=load_yaml('market_backends.yaml').get('order',['eodhd','fmp','alphavantage'])
        for name in order:
            df,s=get_backend(name).fetch(symbol,column,ctx,used);statuses.append(s)
            if not df.empty:return df,statuses
        return pd.DataFrame(),statuses
