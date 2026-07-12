from __future__ import annotations
import os
from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 30
SESSION = requests.Session()
RETRY = Retry(total=3, connect=3, read=3, status=3, backoff_factor=0.8,
              status_forcelist=(429,500,502,503,504), allowed_methods=frozenset({'GET','POST'}),
              respect_retry_after_header=True)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRY)); SESSION.mount('http://', HTTPAdapter(max_retries=RETRY))
SESSION.headers.update({'User-Agent':'PIOS-Capital-Flow-Engine/5.1 (+https://github.com/)','Accept':'application/json,text/csv,text/plain,*/*'})

def env(name: str) -> str: return os.getenv(name,'').strip()

def classify_http(code: int, text: str='') -> str:
    low=(text or '').lower()
    if code==400:return 'BAD_REQUEST'
    if code==401:return 'INVALID_KEY'
    if code==403:return 'PLAN_NOT_SUPPORTED' if any(x in low for x in ('plan','premium','subscription')) else 'PERMISSION_DENIED'
    if code==404:return 'ENDPOINT_OR_SYMBOL_NOT_FOUND'
    if code==408:return 'TIMEOUT'
    if code==429:return 'RATE_LIMIT'
    if 500<=code<=599:return 'UPSTREAM_ERROR'
    return f'HTTP_{code}'

def request(method: str, url: str, **kwargs: Any):
    try:
        r=SESSION.request(method,url,timeout=TIMEOUT,**kwargs)
        try:p=r.json()
        except Exception:p=r.text
        return r,p,''
    except requests.Timeout as e:return None,None,f'TIMEOUT: {e}'
    except requests.RequestException as e:return None,None,f'NETWORK_ERROR: {e}'
