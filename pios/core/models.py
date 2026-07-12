from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import pandas as pd

TAIPEI = timezone(timedelta(hours=8))

def now_taipei() -> str:
    return datetime.now(TAIPEI).strftime('%Y-%m-%d %H:%M:%S%z')

@dataclass
class ProviderStatus:
    source: str
    category: str
    adapter_state: str
    status: str
    error_type: str = ''
    http_code: str = ''
    requires_key: str = 'NO'
    secret_name: str = ''
    history_supported: str = 'NO'
    history_rows: int = 0
    latest_date: str = ''
    data_freshness_days: str = ''
    used_in_model: str = 'NO'
    official_endpoint: str = ''
    official_format_used: str = ''
    detail: str = ''
    retry_policy: str = '3 retries; exponential backoff 0.8; honors Retry-After for 429/5xx'
    updated_at_taipei: str = ''

    def __post_init__(self) -> None:
        self.updated_at_taipei = self.updated_at_taipei or now_taipei()
        self.detail = (self.detail or '')[:800]
        if not self.data_freshness_days and self.latest_date:
            try:
                latest=date.fromisoformat(str(self.latest_date)[:10])
                self.data_freshness_days=str((datetime.now(TAIPEI).date()-latest).days)
            except ValueError:
                self.data_freshness_days='' 


def status(source: str, category: str, state: str, *, adapter_state='IMPLEMENTED', error_type='', http_code='', requires_key=False, secret_name='', history_supported='NO', history_rows=0, latest_date='', used_in_model=False, endpoint='', fmt='', detail='') -> ProviderStatus:
    return ProviderStatus(source, category, adapter_state, state, error_type, http_code,
        'YES' if requires_key else 'NO', secret_name, history_supported, int(history_rows), latest_date, '',
        'YES' if used_in_model else 'NO', endpoint, fmt, detail)

def statuses_to_frame(items: list[ProviderStatus]) -> pd.DataFrame:
    return pd.DataFrame([asdict(x) for x in items])
