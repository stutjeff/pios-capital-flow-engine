from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd
from pios.providers.base import ProviderContext
from pios.core.models import ProviderStatus
class MarketBackend(ABC):
    name='base'
    @abstractmethod
    def fetch(self,symbol:str,column:str,ctx:ProviderContext,used:bool)->tuple[pd.DataFrame,ProviderStatus]:...
