from __future__ import annotations
import pandas as pd
from .base import Provider, ProviderContext, frame, result_status, missing
from .registry import register
from pios.core.http import env, request, classify_http
from pios.core.models import status

@register('eia_wti')
class EiaWtiProvider(Provider):
    def fetch(self,ctx:ProviderContext):
        source='EIA:WTI_RWTC'; col=self.instance.get('column','WTI_OIL'); endpoint='https://api.eia.gov/v2/petroleum/pri/spt/data/'
        fmt='GET api_key,frequency=daily,data[0]=value,facets[series][]=RWTC,sort,length'
        key=env('EIA_API_KEY')
        if not key:return missing(source,'OFFICIAL_ENERGY','EIA_API_KEY',endpoint,fmt,'YES',True)
        params={'api_key':key,'frequency':'daily','data[0]':'value','facets[series][]':'RWTC','sort[0][column]':'period','sort[0][direction]':'asc','start':ctx.start.isoformat(),'end':ctx.today.isoformat(),'length':'5000'}
        r,p,e=request('GET',endpoint,params=params)
        if r is None:return pd.DataFrame(),[status(source,'OFFICIAL_ENERGY','NETWORK_ERROR',error_type=e,requires_key=True,secret_name='EIA_API_KEY',history_supported='YES',used_in_model=True,endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p)); return pd.DataFrame(),[status(source,'OFFICIAL_ENERGY',er,error_type=er,http_code=str(r.status_code),requires_key=True,secret_name='EIA_API_KEY',history_supported='YES',used_in_model=True,endpoint=endpoint,fmt=fmt,detail=str(p))]
        rows=[{'date':x.get('period'),col:x.get('value')} for x in (p or {}).get('response',{}).get('data',[])]
        df=frame(rows,col); return df,[result_status(source,'OFFICIAL_ENERGY',df,requires_key=True,secret_name='EIA_API_KEY',history_supported='YES',used_in_model=True,endpoint=endpoint,fmt=fmt)]
