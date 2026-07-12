from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("gnews")
class GNewsProvider(SimpleEndpointProvider):
    source='GNews'
    category='NEWS'
    endpoint='https://gnews.io/api/v4/search'
    secret='GNEWS_API_KEY'
    requires_key=True
    history='LIMITED'
    official_format='GET /api/v4/search q,lang,max,apikey'
    def build_request(self, ctx):
        return {'params':{'q':'global markets','lang':'en','max':'1','apikey':env('GNEWS_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'articles' in payload
