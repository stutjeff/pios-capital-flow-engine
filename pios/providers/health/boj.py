from __future__ import annotations
from pios.core.http import env
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register("boj")
class BojProvider(SimpleEndpointProvider):
    source='BOJ Time-Series Data Search'
    category='OFFICIAL_MACRO'
    endpoint='https://www.stat-search.boj.or.jp/ssi/mtshtml/fm08_m_1_en.html'
    secret=''
    requires_key=False
    history='YES'
    official_format='GET official BOJ time-series catalogue'
    def build_request(self, ctx):
        return {'headers':{'Accept':'text/html'}}
    def validate(self, payload):
        return isinstance(payload,str) and ('Bank of Japan' in payload or 'BOJ' in payload)
