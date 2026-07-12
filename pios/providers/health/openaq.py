from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("openaq")
class OpenAqProvider(SimpleEndpointProvider):
    source='OpenAQ v3'
    category='ENVIRONMENT'
    endpoint='https://api.openaq.org/v3/parameters/2/latest'
    secret='OPENAQ_API_KEY'
    requires_key=True
    history='LATEST'
    official_format='GET /v3/parameters/2/latest X-API-Key header'
    def build_request(self, ctx):
        return {'headers':{'X-API-Key':env('OPENAQ_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'results' in payload
