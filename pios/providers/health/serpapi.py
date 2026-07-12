from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("serpapi")
class SerpApiProvider(SimpleEndpointProvider):
    source='SerpApi Google Trends'
    category='SEARCH_TRENDS'
    endpoint='https://serpapi.com/search.json'
    secret='SERPAPI_API_KEY'
    requires_key=True
    history='YES'
    official_format='GET search.json engine=google_trends,q,data_type,api_key'
    def build_request(self, ctx):
        return {'params':{'engine':'google_trends','q':'stock market','data_type':'TIMESERIES','api_key':env('SERPAPI_API_KEY')}}
    def validate(self, payload):
        return isinstance(payload,dict)
