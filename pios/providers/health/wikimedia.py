from __future__ import annotations
from datetime import timedelta
from pios.providers.simple import SimpleEndpointProvider
from pios.providers.registry import register

@register('wikimedia')
class WikimediaProvider(SimpleEndpointProvider):
    source='Wikimedia Pageviews'; category='ATTENTION'; history='YES'
    official_format='GET RESTBase pageviews per-article project/access/agent/article/granularity/start/end'
    def build_request(self,ctx):
        s=(ctx.today-timedelta(days=7)).strftime('%Y%m%d'); e=ctx.today.strftime('%Y%m%d')
        self.endpoint=f'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Finance/daily/{s}/{e}'
        return {'headers':{'User-Agent':'PIOS Capital Flow Radar admin@example.com'}}
    def validate(self,payload):return isinstance(payload,dict) and 'items' in payload
