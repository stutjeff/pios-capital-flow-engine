from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("tradingeconomics")
class TradingEconomicsProvider(SimpleEndpointProvider):
    source='Trading Economics'
    category='MARKET_BACKUP'
    endpoint='https://api.tradingeconomics.com/markets/symbol/aapl:us'
    secret='TRADING_ECONOMICS_CREDENTIALS'
    requires_key=False
    history='NO'
    official_format='GET /markets/symbol/{symbol}?c=client:secret (guest:guest supported)'
    def build_request(self, ctx):
        return {'params':{'c':env('TRADING_ECONOMICS_CREDENTIALS') or 'guest:guest'}}
    def validate(self, payload):
        return isinstance(payload,list)
