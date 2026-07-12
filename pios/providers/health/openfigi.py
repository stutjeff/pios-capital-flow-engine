from __future__ import annotations
import pandas as pd
from pios.core.http import env, request, classify_http
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register

@register('openfigi')
class OpenFigiProvider(Provider):
    def fetch(self, ctx: ProviderContext):
        key=env('OPENFIGI_API_KEY'); endpoint='https://api.openfigi.com/v3/mapping'; fmt='POST JSON jobs; X-OPENFIGI-APIKEY optional'
        headers={'Content-Type':'application/json'}
        if key:headers['X-OPENFIGI-APIKEY']=key
        r,p,e=request('POST',endpoint,headers=headers,json=[{'idType':'TICKER','idValue':'SPY','exchCode':'US'}])
        if r is None:return pd.DataFrame(),[status('OpenFIGI','IDENTIFIERS','NETWORK_ERROR',error_type=e.split(':',1)[0],secret_name='OPENFIGI_API_KEY',endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p));return pd.DataFrame(),[status('OpenFIGI','IDENTIFIERS',er,error_type=er,http_code=str(r.status_code),secret_name='OPENFIGI_API_KEY',endpoint=endpoint,fmt=fmt,detail=str(p))]
        ok=isinstance(p,list)
        return pd.DataFrame(),[status('OpenFIGI','IDENTIFIERS','OK' if ok else 'SCHEMA_MISMATCH',error_type='' if ok else 'SCHEMA_MISMATCH',secret_name='OPENFIGI_API_KEY',history_supported='NO',history_rows=len(p) if ok else 0,latest_date=ctx.today.isoformat() if ok else '',endpoint=endpoint,fmt=fmt,detail='mapping response received' if ok else str(p))]
