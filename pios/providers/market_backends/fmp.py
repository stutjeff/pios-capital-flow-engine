from __future__ import annotations
from pios.core.http import env,request
from pios.providers.base import frame,result_status,missing
from .base import MarketBackend
from .registry import register_backend
from .common import failure

@register_backend('fmp')
class FmpBackend(MarketBackend):
    def fetch(self,symbol,column,ctx,used,exchange='US'):
        # FMP stable endpoint accepts US symbols reliably. Non-US symbols are passed
        # with their exchange suffix when available; unsupported plans are classified.
        ticker=symbol if exchange=='US' else f'{symbol}.{exchange}'
        source=f'FMP:{ticker}'
        endpoint='https://financialmodelingprep.com/stable/historical-price-eod/full'
        fmt='GET symbol,from,to,apikey'
        key=env('FMP_API_KEY')
        if not key:
            df,items=missing(source,'MARKET_DATA','FMP_API_KEY',endpoint,fmt,'YES',used)
            return df,items[0]
        r,p,e=request('GET',endpoint,params={'symbol':ticker,'from':ctx.start.isoformat(),'to':ctx.today.isoformat(),'apikey':key})
        if r is None or not r.ok:return failure(source,'FMP_API_KEY',endpoint,fmt,used,r,p,e)
        data=p.get('historical',p) if isinstance(p,dict) else p
        rows=[{'date':x.get('date'),column:x.get('adjClose') or x.get('close')} for x in data] if isinstance(data,list) else []
        df=frame(rows,column)
        return df,result_status(source,'MARKET_DATA',df,requires_key=True,secret_name='FMP_API_KEY',history_supported='YES',used_in_model=used,endpoint=endpoint,fmt=fmt)
