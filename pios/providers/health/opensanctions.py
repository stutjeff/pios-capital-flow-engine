from __future__ import annotations
import pandas as pd
from pios.core.http import env, request, classify_http
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register

@register('opensanctions')
class OpenSanctionsProvider(Provider):
    def fetch(self, ctx: ProviderContext):
        key=env('OPENSANCTIONS_API_KEY'); endpoint='https://api.opensanctions.org/match/default'; fmt='POST JSON queries; Authorization: ApiKey'
        if not key:return pd.DataFrame(),[status('OpenSanctions','COMPLIANCE','MISSING_KEY',error_type='MISSING_KEY',requires_key=True,secret_name='OPENSANCTIONS_API_KEY',endpoint=endpoint,fmt=fmt,detail='GitHub Secret OPENSANCTIONS_API_KEY is missing.')]
        r,p,e=request('POST',endpoint,headers={'Authorization':f'ApiKey {key}','Content-Type':'application/json'},json={'queries':{'q1':{'schema':'Company','properties':{'name':['Apple Inc']}}}})
        if r is None:return pd.DataFrame(),[status('OpenSanctions','COMPLIANCE','NETWORK_ERROR',error_type=e.split(':',1)[0],requires_key=True,secret_name='OPENSANCTIONS_API_KEY',endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p));return pd.DataFrame(),[status('OpenSanctions','COMPLIANCE',er,error_type=er,http_code=str(r.status_code),requires_key=True,secret_name='OPENSANCTIONS_API_KEY',endpoint=endpoint,fmt=fmt,detail=str(p))]
        ok=isinstance(p,dict)
        return pd.DataFrame(),[status('OpenSanctions','COMPLIANCE','OK' if ok else 'SCHEMA_MISMATCH',requires_key=True,secret_name='OPENSANCTIONS_API_KEY',history_rows=1 if ok else 0,latest_date=ctx.today.isoformat() if ok else '',endpoint=endpoint,fmt=fmt,detail='match endpoint accepted' if ok else str(p))]
