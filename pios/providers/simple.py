from __future__ import annotations
from typing import Any, Callable
import pandas as pd
from pios.core.http import env, request, classify_http
from pios.core.models import ProviderStatus, status
from .base import Provider, ProviderContext

Validator = Callable[[Any], bool]

class SimpleEndpointProvider(Provider):
    source = ""
    category = "DIAGNOSTIC"
    endpoint = ""
    method = "GET"
    secret = ""
    requires_key = False
    history = "NO"
    official_format = ""
    used_in_model = False

    def build_request(self, ctx: ProviderContext) -> dict[str, Any]:
        return {}

    def validate(self, payload: Any) -> bool:
        return payload is not None

    def success_rows(self, payload: Any) -> int:
        if isinstance(payload, list): return len(payload)
        if isinstance(payload, dict):
            for key in ("data", "results", "items", "articles", "observations"):
                value = payload.get(key)
                if isinstance(value, list): return len(value)
        return 1

    def fetch(self, ctx: ProviderContext) -> tuple[pd.DataFrame, list[ProviderStatus]]:
        key = env(self.secret) if self.secret else ""
        if self.requires_key and not key:
            return pd.DataFrame(), [status(self.source,self.category,"MISSING_KEY",error_type="MISSING_KEY",requires_key=True,secret_name=self.secret,history_supported=self.history,used_in_model=self.used_in_model,endpoint=self.endpoint,fmt=self.official_format,detail=f"GitHub Secret {self.secret} is missing.")]
        req = self.build_request(ctx)
        r,p,e = request(self.method,self.endpoint,**req)
        if r is None:
            return pd.DataFrame(), [status(self.source,self.category,"NETWORK_ERROR",error_type=e.split(':',1)[0],requires_key=self.requires_key,secret_name=self.secret,history_supported=self.history,used_in_model=self.used_in_model,endpoint=self.endpoint,fmt=self.official_format,detail=e)]
        if not r.ok:
            err=classify_http(r.status_code,str(p))
            return pd.DataFrame(), [status(self.source,self.category,err,error_type=err,http_code=str(r.status_code),requires_key=self.requires_key,secret_name=self.secret,history_supported=self.history,used_in_model=self.used_in_model,endpoint=self.endpoint,fmt=self.official_format,detail=str(p))]
        if not self.validate(p):
            return pd.DataFrame(), [status(self.source,self.category,"SCHEMA_MISMATCH",error_type="SCHEMA_MISMATCH",http_code=str(r.status_code),requires_key=self.requires_key,secret_name=self.secret,history_supported=self.history,used_in_model=self.used_in_model,endpoint=self.endpoint,fmt=self.official_format,detail=f"Unexpected payload type/keys: {type(p).__name__}")]
        return pd.DataFrame(), [status(self.source,self.category,"OK",requires_key=self.requires_key,secret_name=self.secret,history_supported=self.history,history_rows=self.success_rows(p),latest_date=ctx.today.isoformat(),used_in_model=self.used_in_model,endpoint=self.endpoint,fmt=self.official_format,detail="official endpoint responded with expected schema")]
