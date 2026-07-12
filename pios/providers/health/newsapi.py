from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("newsapi")
class NewsApiProvider(SimpleEndpointProvider):
    source='NewsAPI'
    category='NEWS'
    endpoint='https://newsapi.org/v2/everything'
    secret='NEWSAPI_KEY'
    requires_key=True
    history='PLAN_DEPENDENT'
    official_format='GET /v2/everything q,pageSize,sortBy,apiKey'
    def build_request(self, ctx):
        return {'params':{'q':'global markets','pageSize':'1','sortBy':'publishedAt','apiKey':env('NEWSAPI_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and payload.get('status')=='ok'
