from __future__ import annotations
import pandas as pd
from .base import Provider,ProviderContext,frame,result_status
from .registry import register
from pios.core.http import request,classify_http
from pios.core.models import status

@register('treasury_average')
class TreasuryProvider(Provider):
    def fetch(self,ctx:ProviderContext):
        source='US Treasury:Average Interest Rates'; endpoint='https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates'; fmt='GET filter=record_date:gte,sort,page[size],format=json'
        params={'filter':f'record_date:gte:{ctx.start.isoformat()}','sort':'record_date','page[size]':'5000','format':'json'}
        r,p,e=request('GET',endpoint,params=params)
        if r is None:return pd.DataFrame(),[status(source,'OFFICIAL_RATES','NETWORK_ERROR',error_type=e,history_supported='YES',endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:
            er=classify_http(r.status_code,str(p)); return pd.DataFrame(),[status(source,'OFFICIAL_RATES',er,error_type=er,http_code=str(r.status_code),history_supported='YES',endpoint=endpoint,fmt=fmt,detail=str(p))]
        rows=[]
        for x in (p or {}).get('data',[]):
            if 'Treasury Notes' in str(x.get('security_desc','')): rows.append({'date':x.get('record_date'),'TREASURY_AVG_NOTE_RATE':x.get('avg_interest_rate_amt')})
        df=frame(rows,'TREASURY_AVG_NOTE_RATE'); return df,[result_status(source,'OFFICIAL_RATES',df,history_supported='YES',endpoint=endpoint,fmt=fmt)]
