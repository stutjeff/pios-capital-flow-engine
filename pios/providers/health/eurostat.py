from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("eurostat")
class EurostatProvider(SimpleEndpointProvider):
    source='Eurostat'
    category='OFFICIAL_MACRO'
    endpoint='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/teina011'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET dissemination statistics 1.0 data/{dataset}'
    def build_request(self, ctx):
        return {'params':{'lang':'en','geo':'EU27_2020','sinceTimePeriod':'2024-Q1'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'value' in payload
