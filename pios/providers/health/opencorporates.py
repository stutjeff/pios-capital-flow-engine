from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("opencorporates")
class OpenCorporatesProvider(SimpleEndpointProvider):
    source='OpenCorporates'
    category='CORPORATE'
    endpoint='https://api.opencorporates.com/v0.4/companies/search'
    secret='OPENCORPORATES_API_KEY'
    requires_key=False
    history='NO'
    official_format='GET /v0.4/companies/search q,api_token(optional)'
    def build_request(self, ctx):
        p={'q':'Apple'}; key=env('OPENCORPORATES_API_KEY'); p.update({'api_token':key} if key else {}); return {'params':p}
    def validate(self, payload):
        return isinstance(payload,dict) and 'results' in payload
