from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("worldbank")
class WorldBankProvider(SimpleEndpointProvider):
    source='World Bank API v2'
    category='OFFICIAL_MACRO'
    endpoint='https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.MKTP.CD'
    secret=''
    requires_key=False
    history='ANNUAL'
    official_format='GET /v2/country/{country}/indicator/{indicator}?format=json'
    def build_request(self, ctx):
        return {'params':{'format':'json','per_page':'5'}}
    def validate(self, payload):
        return isinstance(payload,list) and len(payload)>=2
