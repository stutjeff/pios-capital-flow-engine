from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("census")
class CensusProvider(SimpleEndpointProvider):
    source='US Census'
    category='OFFICIAL_MACRO'
    endpoint='https://api.census.gov/data/2024/acs/acs5/profile'
    secret='CENSUS_API_KEY'
    requires_key=False
    history='ANNUAL'
    official_format='GET ACS5 profile get,for,key(optional)'
    def build_request(self, ctx):
        p={'get':'NAME,DP03_0001E','for':'us:1'}; key=env('CENSUS_API_KEY'); p.update({'key':key} if key else {}); return {'params':p}
    def validate(self, payload):
        return isinstance(payload,list)
