from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("nyt")
class NytProvider(SimpleEndpointProvider):
    source='New York Times'
    category='NEWS'
    endpoint='https://api.nytimes.com/svc/search/v2/articlesearch.json'
    secret='NYTIMES_API_KEY'
    requires_key=True
    history='YES'
    official_format='GET Article Search v2 q,api-key'
    def build_request(self, ctx):
        return {'params':{'q':'global markets','api-key':env('NYTIMES_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and payload.get('status')=='OK'
