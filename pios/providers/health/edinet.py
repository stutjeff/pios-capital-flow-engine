from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("edinet")
class EdinetProvider(SimpleEndpointProvider):
    source='EDINET API v2'
    category='OFFICIAL_FILINGS'
    endpoint='https://api.edinet-fsa.go.jp/api/v2/documents.json'
    secret='EDINET_API_KEY'
    requires_key=True
    history='DAILY'
    official_format='GET date,type=2,Subscription-Key'
    def build_request(self, ctx):
        return {'params':{'date':ctx.today.isoformat(),'type':'2','Subscription-Key':env('EDINET_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'metadata' in payload
