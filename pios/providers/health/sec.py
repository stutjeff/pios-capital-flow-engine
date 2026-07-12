from __future__ import annotations

import pandas as pd

from pios.core.http import env, request, classify_http
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register


@register("sec")
class SecProvider(Provider):
    """SEC EDGAR public-data health check using the declared User-Agent policy."""

    source = "SEC EDGAR"
    category = "OFFICIAL_FILINGS"
    endpoint = "https://www.sec.gov/files/company_tickers.json"
    official_format = "GET with declared User-Agent and gzip/deflate support"
    history = "CURRENT"
    used_in_model = False

    def fetch(self, ctx: ProviderContext):
        user_agent = env("SEC_USER_AGENT")
        if not user_agent:
            return pd.DataFrame(), [
                status(
                    self.source,
                    self.category,
                    "MISSING_CONFIGURATION",
                    error_type="MISSING_CONFIGURATION",
                    requires_key=False,
                    secret_name="SEC_USER_AGENT",
                    history_supported=self.history,
                    used_in_model=self.used_in_model,
                    endpoint=self.endpoint,
                    fmt=self.official_format,
                    detail="GitHub Secret SEC_USER_AGENT is required for SEC fair-access identification.",
                )
            ]

        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        }
        response, payload, error = request("GET", self.endpoint, headers=headers)

        if response is None:
            return pd.DataFrame(), [
                status(
                    self.source,
                    self.category,
                    "NETWORK_ERROR",
                    error_type=(error or "NETWORK_ERROR").split(":", 1)[0],
                    requires_key=False,
                    secret_name="SEC_USER_AGENT",
                    history_supported=self.history,
                    used_in_model=self.used_in_model,
                    endpoint=self.endpoint,
                    fmt=self.official_format,
                    detail=error,
                )
            ]

        if not response.ok:
            error_type = classify_http(response.status_code, str(payload))
            return pd.DataFrame(), [
                status(
                    self.source,
                    self.category,
                    error_type,
                    error_type=error_type,
                    http_code=str(response.status_code),
                    requires_key=False,
                    secret_name="SEC_USER_AGENT",
                    history_supported=self.history,
                    used_in_model=self.used_in_model,
                    endpoint=self.endpoint,
                    fmt=self.official_format,
                    detail=str(payload)[:500],
                )
            ]

        if not isinstance(payload, dict) or not payload:
            return pd.DataFrame(), [
                status(
                    self.source,
                    self.category,
                    "SCHEMA_MISMATCH",
                    error_type="SCHEMA_MISMATCH",
                    http_code=str(response.status_code),
                    requires_key=False,
                    secret_name="SEC_USER_AGENT",
                    history_supported=self.history,
                    used_in_model=self.used_in_model,
                    endpoint=self.endpoint,
                    fmt=self.official_format,
                    detail=f"Expected a non-empty JSON object, received {type(payload).__name__}.",
                )
            ]

        return pd.DataFrame(), [
            status(
                self.source,
                self.category,
                "OK",
                requires_key=False,
                secret_name="SEC_USER_AGENT",
                history_supported=self.history,
                history_rows=len(payload),
                latest_date=ctx.today.isoformat(),
                used_in_model=self.used_in_model,
                endpoint=self.endpoint,
                fmt=self.official_format,
                detail="SEC endpoint responded with the expected company-ticker JSON schema.",
            )
        ]
