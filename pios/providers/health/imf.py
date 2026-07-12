from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("imf")
class ImfProvider(SimpleEndpointProvider):
    source='IMF DataMapper'
    category='OFFICIAL_MACRO'
    endpoint='https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/USA'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET /external/datamapper/api/v1/{indicator}/{country}'
    def build_request(self, ctx):
        return {}
    def validate(self, payload):
        return isinstance(payload,dict)
