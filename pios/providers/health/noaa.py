from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("noaa")
class NoaaProvider(SimpleEndpointProvider):
    source='NOAA NCEI CDO v2'
    category='ENVIRONMENT'
    endpoint='https://www.ncei.noaa.gov/cdo-web/api/v2/datasets'
    secret='NOAA_CDO_TOKEN'
    requires_key=True
    history='YES'
    official_format='GET /cdo-web/api/v2/datasets token header'
    def build_request(self, ctx):
        return {'params':{'limit':'1'},'headers':{'token':env('NOAA_CDO_TOKEN')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'results' in payload
