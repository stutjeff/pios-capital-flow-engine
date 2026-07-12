from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("gdelt")
class GdeltProvider(SimpleEndpointProvider):
    source='GDELT DOC 2.0'
    category='NEWS'
    endpoint='https://api.gdeltproject.org/api/v2/doc/doc'
    secret=''
    requires_key=False
    history='ROLLING'
    official_format='GET DOC 2.0 query,mode=ArtList,format=json,maxrecords'
    def build_request(self, ctx):
        return {'params':{'query':'global markets','mode':'ArtList','format':'json','maxrecords':'1'}}
    def validate(self, payload):
        return isinstance(payload,dict)
