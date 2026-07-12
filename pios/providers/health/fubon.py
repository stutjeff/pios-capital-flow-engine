from __future__ import annotations
import importlib.util
import pandas as pd
from pios.core.models import status
from pios.providers.base import Provider, ProviderContext
from pios.providers.registry import register
@register('fubon_sdk')
class FubonSdkProvider(Provider):
    def fetch(self,ctx):
        try:pkg=importlib.util.find_spec('fubon_neo')
        except Exception:pkg=None
        state='SDK_AVAILABLE' if pkg else 'SDK_NOT_INSTALLED'
        return pd.DataFrame(),[status('富邦 Neo','BROKER_SDK',state,adapter_state='OFFICIAL_SDK' if pkg else 'OFFICIAL_SDK_OPTIONAL',error_type='' if pkg else 'PACKAGE_MISSING',requires_key=True,secret_name='FUBON_ID,FUBON_PASSWORD,FUBON_CERT_PATH,FUBON_CERT_PASSWORD',history_supported='BROKER_DEPENDENT',endpoint='Fubon Neo Python SDK',fmt='Official SDK authentication; account login not performed in health test',detail='SDK package detected.' if pkg else 'Optional broker SDK not installed; not required for the global model.')]
