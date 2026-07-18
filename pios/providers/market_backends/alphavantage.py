from __future__ import annotations
from pios.core.http import env,request
from pios.providers.base import frame,result_status,missing
from .base import MarketBackend
from .registry import register_backend
from .common import failure

@register_backend('alphavantage')
class AlphaVantageBackend(MarketBackend):
    def fetch(self,symbol,column,ctx,used,exchange='US'):
        ticker=symbol if exchange=='US' else f'{symbol}.{exchange}'
        source=f'AlphaVantage:{ticker}'
        endpoint='https://www.alphavantage.co/query'
        fmt='GET function=TIME_SERIES_DAILY,symbol,outputsize=compact,apikey'
        key=env('ALPHAVANTAGE_API_KEY')
        if not key:
            df,items=missing(source,'MARKET_DATA','ALPHAVANTAGE_API_KEY',endpoint,fmt,'LIMITED_100',used)
            return df,items[0]
        r,p,e=request('GET',endpoint,params={'function':'TIME_SERIES_DAILY','symbol':ticker,'outputsize':'compact','apikey':key})
        if r is None or not r.ok:return failure(source,'ALPHAVANTAGE_API_KEY',endpoint,fmt,used,r,p,e,'LIMITED_100')
        series=(p or {}).get('Time Series (Daily)',{}) if isinstance(p,dict) else {}
        rows=[{'date':d,column:x.get('5. adjusted close') or x.get('4. close')} for d,x in series.items()]
        df=frame(rows,column)
        return df,result_status(source,'MARKET_DATA',df,requires_key=True,secret_name='ALPHAVANTAGE_API_KEY',history_supported='LIMITED_100',used_in_model=used,endpoint=endpoint,fmt=fmt)
