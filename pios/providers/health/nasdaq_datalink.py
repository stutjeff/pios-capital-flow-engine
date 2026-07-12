from __future__ import annotations
import pandas as pd
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register
@register('nasdaq_datalink_disabled')
class NasdaqDataLinkDisabled(Provider):
    def fetch(self,ctx):return pd.DataFrame(),[status('Nasdaq Data Link','OPTIONAL_ENTERPRISE','DISABLED',adapter_state='OFFICIAL_DISABLED',error_type='ENTERPRISE_DATASETS',requires_key=True,secret_name='NASDAQ_DATA_LINK_API_KEY',history_supported='PLAN_DEPENDENT',endpoint='https://data.nasdaq.com/api/v3/',fmt='Not called by daily workflow',detail='Disabled by design because required datasets are plan dependent.')]
