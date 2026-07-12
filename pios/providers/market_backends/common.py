from __future__ import annotations
import pandas as pd
from pios.core.models import status
from pios.core.http import classify_http

def failure(source,secret,endpoint,fmt,used,r,p,e,history='YES'):
    if r is None:return pd.DataFrame(),status(source,'MARKET_DATA','NETWORK_ERROR',error_type=(e or 'NETWORK_ERROR').split(':',1)[0],requires_key=True,secret_name=secret,history_supported=history,used_in_model=used,endpoint=endpoint,fmt=fmt,detail=e)
    er=classify_http(r.status_code,str(p));return pd.DataFrame(),status(source,'MARKET_DATA',er,error_type=er,http_code=str(r.status_code),requires_key=True,secret_name=secret,history_supported=history,used_in_model=used,endpoint=endpoint,fmt=fmt,detail=str(p))
