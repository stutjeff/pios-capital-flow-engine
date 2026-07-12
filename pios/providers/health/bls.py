from __future__ import annotations
import pandas as pd
from pios.core.http import env, request, classify_http
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register

@register('bls')
class BlsProvider(Provider):
    def fetch(self, ctx: ProviderContext):
        payload={'seriesid':['CUUR0000SA0'],'startyear':str(ctx.start.year),'endyear':str(ctx.today.year)}
        key=env('BLS_API_KEY')
        if key: payload['registrationkey']=key
        endpoint='https://api.bls.gov/publicAPI/v2/timeseries/data/'
        fmt='POST JSON seriesid,startyear,endyear,registrationkey(optional)'
        r,p,e=request('POST',endpoint,json=payload)
        if r is None:return pd.DataFrame(),[status('BLS','OFFICIAL_MACRO','NETWORK_ERROR',error_type=e.split(':',1)[0],secret_name='BLS_API_KEY',history_supported='YES',endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p));return pd.DataFrame(),[status('BLS','OFFICIAL_MACRO',er,error_type=er,http_code=str(r.status_code),secret_name='BLS_API_KEY',history_supported='YES',endpoint=endpoint,fmt=fmt,detail=str(p))]
        ok=isinstance(p,dict) and p.get('status')=='REQUEST_SUCCEEDED'
        rows=sum(len(x.get('data',[])) for x in p.get('Results',{}).get('series',[])) if ok else 0
        return pd.DataFrame(),[status('BLS','OFFICIAL_MACRO','OK' if ok else 'SCHEMA_MISMATCH',error_type='' if ok else 'SCHEMA_MISMATCH',secret_name='BLS_API_KEY',history_supported='YES',history_rows=rows,latest_date=ctx.today.isoformat() if ok else '',endpoint=endpoint,fmt=fmt,detail='official v2 request succeeded' if ok else str(p))]
