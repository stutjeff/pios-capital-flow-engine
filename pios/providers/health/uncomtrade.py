from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("uncomtrade")
class UnComtradeProvider(SimpleEndpointProvider):
    source='UN Comtrade'
    category='OFFICIAL_TRADE'
    endpoint='https://comtradeapi.un.org/public/v1/preview/C/A/HS'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET public v1 preview/{type}/{freq}/{classification} query params'
    def build_request(self, ctx):
        return {'params':{'period':str(ctx.today.year-1),'reporterCode':'842','cmdCode':'TOTAL','flowCode':'M','partnerCode':'0','partner2Code':'0','customsCode':'C00','motCode':'0','maxRecords':'1'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'data' in payload
