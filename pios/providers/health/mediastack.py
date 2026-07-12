from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("mediastack")
class MediastackProvider(SimpleEndpointProvider):
    source='Mediastack'
    category='NEWS'
    endpoint='https://api.mediastack.com/v1/news'
    secret='MEDIASTACK_API_KEY'
    requires_key=True
    history='PLAN_DEPENDENT'
    official_format='GET /v1/news access_key,keywords,limit,languages'
    def build_request(self, ctx):
        return {'params':{'access_key':env('MEDIASTACK_API_KEY'),'keywords':'global markets','limit':'1','languages':'en'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'data' in payload
