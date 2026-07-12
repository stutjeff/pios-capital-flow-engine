from __future__ import annotations
import pandas as pd
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register
@register('stooq_disabled')
class StooqDisabled(Provider):
    def fetch(self,ctx):return pd.DataFrame(),[status('Stooq','UNOFFICIAL_SOURCE','DISABLED',adapter_state='UNOFFICIAL_DISABLED',error_type='NOT_OFFICIAL_API',history_supported='YES',endpoint='https://stooq.com/',fmt='Not called',detail='Removed from active path because there is no official documented API contract.')]
