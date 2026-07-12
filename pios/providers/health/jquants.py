from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("jquants")
class JQuantsProvider(SimpleEndpointProvider):
    source='J-Quants V2:投資部門別'
    category='OFFICIAL_FLOW'
    endpoint='https://api.jquants.com/v2/equities/investor-types'
    secret='JQUANTS_API_KEY'
    requires_key=True
    history='YES'
    official_format='GET /v2/equities/investor-types; x-api-key header; from,to'
    def build_request(self, ctx):
        return {'params':{'from':ctx.start.isoformat(),'to':ctx.today.isoformat()},'headers':{'x-api-key':env('JQUANTS_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'data' in payload
