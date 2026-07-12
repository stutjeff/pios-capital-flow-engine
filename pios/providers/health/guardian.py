from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("guardian")
class GuardianProvider(SimpleEndpointProvider):
    source='The Guardian'
    category='NEWS'
    endpoint='https://content.guardianapis.com/search'
    secret='GUARDIAN_API_KEY'
    requires_key=True
    history='YES'
    official_format='GET /search q,page-size,api-key'
    def build_request(self, ctx):
        return {'params':{'q':'global markets','page-size':'1','api-key':env('GUARDIAN_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and payload.get('response',{}).get('status')=='ok'
