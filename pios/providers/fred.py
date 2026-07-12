from __future__ import annotations
import pandas as pd
from .base import Provider, ProviderContext, frame, result_status, missing
from .registry import register
from pios.core.http import env, request, classify_http
from pios.core.models import status

@register('fred')
class FredProvider(Provider):
    def fetch(self, ctx: ProviderContext):
        sid=self.instance['series_id']; col=self.instance['column']; used=bool(self.instance.get('used_in_model',True))
        source=f'FRED:{sid}'; endpoint='https://api.stlouisfed.org/fred/series/observations'
        fmt='GET series_id,api_key,file_type=json,observation_start,observation_end'
        key=env('FRED_API_KEY')
        if not key:return missing(source,'OFFICIAL_MACRO','FRED_API_KEY',endpoint,fmt,'YES',used)
        r,p,e=request('GET',endpoint,params={'series_id':sid,'api_key':key,'file_type':'json','observation_start':ctx.start.isoformat(),'observation_end':ctx.today.isoformat(),'sort_order':'asc'})
        if r is None:return pd.DataFrame(),[status(source,'OFFICIAL_MACRO','NETWORK_ERROR',error_type=e,requires_key=True,secret_name='FRED_API_KEY',history_supported='YES',used_in_model=used,endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p)); return pd.DataFrame(),[status(source,'OFFICIAL_MACRO',er,error_type=er,http_code=str(r.status_code),requires_key=True,secret_name='FRED_API_KEY',history_supported='YES',used_in_model=used,endpoint=endpoint,fmt=fmt,detail=str(p))]
        rows=[{'date':x.get('date'),col:x.get('value')} for x in (p or {}).get('observations',[]) if x.get('value') not in (None,'','.')]
        df=frame(rows,col); return df,[result_status(source,'OFFICIAL_MACRO',df,requires_key=True,secret_name='FRED_API_KEY',history_supported='YES',used_in_model=used,endpoint=endpoint,fmt=fmt)]
