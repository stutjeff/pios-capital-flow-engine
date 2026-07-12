from __future__ import annotations
from pios.core.http import env,request
from pios.providers.base import frame,result_status,missing
from .base import MarketBackend
from .registry import register_backend
from .common import failure
@register_backend('eodhd')
class EodhdBackend(MarketBackend):
    def fetch(self,symbol,column,ctx,used):
        source=f'EODHD:{symbol}.US';endpoint=f'https://eodhd.com/api/eod/{symbol}.US';fmt='GET api_token,fmt=json,from,to,period=d,order=a';key=env('EODHD_API_KEY')
        if not key:return missing(source,'MARKET_DATA','EODHD_API_KEY',endpoint,fmt,'YES',used)[0],missing(source,'MARKET_DATA','EODHD_API_KEY',endpoint,fmt,'YES',used)[1][0]
        r,p,e=request('GET',endpoint,params={'api_token':key,'fmt':'json','from':ctx.start.isoformat(),'to':ctx.today.isoformat(),'period':'d','order':'a'})
        if r is None or not r.ok:return failure(source,'EODHD_API_KEY',endpoint,fmt,used,r,p,e)
        rows=[{'date':x.get('date'),column:x.get('adjusted_close') or x.get('close')} for x in p] if isinstance(p,list) else []
        df=frame(rows,column);return df,result_status(source,'MARKET_DATA',df,requires_key=True,secret_name='EODHD_API_KEY',history_supported='YES',used_in_model=used,endpoint=endpoint,fmt=fmt)
