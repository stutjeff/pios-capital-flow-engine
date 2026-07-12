from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("bea")
class BeaProvider(SimpleEndpointProvider):
    source='BEA'
    category='OFFICIAL_MACRO'
    endpoint='https://apps.bea.gov/api/data'
    secret='BEA_API_KEY'
    requires_key=True
    history='YES'
    official_format='GET UserID,method=GetData,datasetname=NIPA,TableName,Frequency,Year,ResultFormat'
    def build_request(self, ctx):
        return {'params':{'UserID':env('BEA_API_KEY'),'method':'GetData','datasetname':'NIPA','TableName':'T10101','Frequency':'Q','Year':'X','ResultFormat':'JSON'}}
    def validate(self, payload):
        return isinstance(payload,dict) and 'BEAAPI' in payload
