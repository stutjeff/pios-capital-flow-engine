from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("oecd")
class OecdProvider(SimpleEndpointProvider):
    source='OECD SDMX'
    category='OFFICIAL_MACRO'
    endpoint='https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.1/.?startPeriod=2025-01&format=csvfile'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET SDMX REST v1 data; Accept text/csv'
    def build_request(self, ctx):
        return {'headers':{'Accept':'text/csv'}}
    def validate(self, payload):
        return isinstance(payload,str) and len(payload)>20
