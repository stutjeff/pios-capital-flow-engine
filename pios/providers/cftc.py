from __future__ import annotations
import io,zipfile
import pandas as pd
from .base import Provider,ProviderContext,frame,result_status
from .registry import register
from pios.core.http import request
from pios.core.models import status

@register('cftc_cot')
class CftcProvider(Provider):
    def fetch(self,ctx:ProviderContext):
        source='CFTC:COT_TFF'; endpoint='https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip'; fmt='GET official annual Traders in Financial Futures ZIP'
        # Official annual file; current year derived dynamically.
        endpoint=f'https://www.cftc.gov/files/dea/history/fut_fin_txt_{ctx.today.year}.zip'
        r,p,e=request('GET',endpoint)
        if r is None:return pd.DataFrame(),[status(source,'OFFICIAL_FLOW','NETWORK_ERROR',error_type=e,history_supported='WEEKLY',endpoint=endpoint,fmt=fmt,detail=e)]
        if not r.ok:return pd.DataFrame(),[status(source,'OFFICIAL_FLOW',f'HTTP_{r.status_code}',error_type=f'HTTP_{r.status_code}',http_code=str(r.status_code),history_supported='WEEKLY',endpoint=endpoint,fmt=fmt,detail=str(p))]
        try:
            z=zipfile.ZipFile(io.BytesIO(r.content)); name=z.namelist()[0]
            raw=pd.read_csv(z.open(name),low_memory=False)
            def col_like(*needles):
                for c in raw.columns:
                    low=c.lower()
                    if all(n.lower() in low for n in needles):return c
                return None
            date_col=col_like('report_date') or col_like('as_of_date')
            market_col=col_like('market_and_exchange') or col_like('market')
            long_col=col_like('asset_mgr','long')
            short_col=col_like('asset_mgr','short')
            if not all([date_col,market_col,long_col,short_col]):raise ValueError('expected TFF columns not found')
            sub=raw[raw[market_col].astype(str).str.contains('E-MINI S&P 500',case=False,na=False)].copy()
            sub['CFTC_SP500_ASSET_MGR_NET']=pd.to_numeric(sub[long_col],errors='coerce')-pd.to_numeric(sub[short_col],errors='coerce')
            df=frame([{'date':d,'CFTC_SP500_ASSET_MGR_NET':v} for d,v in zip(sub[date_col],sub['CFTC_SP500_ASSET_MGR_NET'])],'CFTC_SP500_ASSET_MGR_NET')
            return df,[result_status(source,'OFFICIAL_FLOW',df,history_supported='WEEKLY',endpoint=endpoint,fmt=fmt)]
        except Exception as ex:
            return pd.DataFrame(),[status(source,'OFFICIAL_FLOW','PARSE_ERROR',error_type=type(ex).__name__,history_supported='WEEKLY',endpoint=endpoint,fmt=fmt,detail=repr(ex))]
