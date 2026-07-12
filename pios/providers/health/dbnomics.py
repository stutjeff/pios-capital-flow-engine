from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("dbnomics")
class DbnomicsProvider(SimpleEndpointProvider):
    source='DBnomics'
    category='PUBLIC_MACRO'
    endpoint='https://api.db.nomics.world/v22/series/IMF/WEO:2025-APR/USA.NGDP_RPCH'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET /v22/series/{provider}/{dataset}/{series}?observations=1'
    def build_request(self, ctx):
        return {'params':{'observations':'1'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'series' in payload
