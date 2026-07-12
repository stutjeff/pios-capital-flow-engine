from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("tdcc")
class TdccProvider(SimpleEndpointProvider):
    source='TDCC:集保戶股權分散表'
    category='OFFICIAL_FLOW'
    endpoint='https://openapi.tdcc.com.tw/v1/opendata/1-5'
    secret=''
    requires_key=False
    history='WEEKLY'
    official_format='GET /v1/opendata/1-5 official TDCC OpenAPI JSON'
    def build_request(self, ctx):
        return {}
    def validate(self, payload):
        return isinstance(payload,list)
