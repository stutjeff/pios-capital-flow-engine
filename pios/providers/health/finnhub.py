from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("finnhub")
class FinnhubProvider(SimpleEndpointProvider):
    source='Finnhub'
    category='MARKET_BACKUP'
    endpoint='https://finnhub.io/api/v1/quote'
    secret='FINNHUB_API_KEY'
    requires_key=True
    history='NO'
    official_format='GET /api/v1/quote symbol,token'
    def build_request(self, ctx):
        return {'params':{'symbol':'AAPL','token':env('FINNHUB_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'c' in payload
