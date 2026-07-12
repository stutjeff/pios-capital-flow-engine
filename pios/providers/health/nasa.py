from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("nasa")
class NasaProvider(SimpleEndpointProvider):
    source='NASA APOD'
    category='SCIENCE'
    endpoint='https://api.nasa.gov/planetary/apod'
    secret='NASA_API_KEY'
    requires_key=False
    history='YES'
    official_format='GET /planetary/apod api_key'
    def build_request(self, ctx):
        return {'params':{'api_key':env('NASA_API_KEY') or 'DEMO_KEY'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'date' in payload
