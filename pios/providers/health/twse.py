from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("twse")
class TwseProvider(SimpleEndpointProvider):
    source='TWSE:三大法人買賣金額'
    category='OFFICIAL_FLOW'
    endpoint='https://openapi.twse.com.tw/v1/fund/BFI82U'
    secret=''
    requires_key=False
    history='DAILY_SNAPSHOT'
    official_format='GET official TWSE OpenAPI JSON'
    def build_request(self, ctx):
        return {}
    def validate(self, payload):
        return isinstance(payload,list) or (isinstance(payload,dict) and any(k in payload for k in ('data','result','results')))
