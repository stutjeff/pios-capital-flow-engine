from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("marketaux")
class MarketauxProvider(SimpleEndpointProvider):
    source='Marketaux'
    category='NEWS'
    endpoint='https://api.marketaux.com/v1/news/all'
    secret='MARKETAUX_API_KEY'
    requires_key=True
    history='PLAN_DEPENDENT'
    official_format='GET /v1/news/all symbols,limit,api_token'
    def build_request(self, ctx):
        return {'params':{'symbols':'SPY,QQQ','limit':'1','api_token':env('MARKETAUX_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'data' in payload
