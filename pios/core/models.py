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
    market_date: str = ''
    market_session: str = ''
    region: str = ''
    data_lag_hours: str = ''
    data_type: str = ''
    used_in_model: str = 'NO'
    official_endpoint: str = ''
    official_format_used: str = ''
    detail: str = ''
    retry_policy: str = '3 retries; exponential backoff 0.8; honors Retry-After for 429/5xx'
    updated_at_taipei: str = ''

    def __post_init__(self) -> None:
        self.updated_at_taipei = self.updated_at_taipei or now_taipei()
        self.detail = (self.detail or '')[:800]
        self.market_date = self.market_date or self.latest_date
        if not self.data_freshness_days and self.latest_date:
            try:
                latest=date.fromisoformat(str(self.latest_date)[:10])
                self.data_freshness_days=str((datetime.now(TAIPEI).date()-latest).days)
            except ValueError:
                self.data_freshness_days='' 


def status(source: str, category: str, state: str, *, adapter_state='IMPLEMENTED', error_type='', http_code='', requires_key=False, secret_name='', history_supported='NO', history_rows=0, latest_date='', used_in_model=False, endpoint='', fmt='', detail='', market_session='', region='', data_lag_hours='', data_type='') -> ProviderStatus:
    return ProviderStatus(
        source=source, category=category, adapter_state=adapter_state, status=state,
        error_type=error_type, http_code=http_code, requires_key='YES' if requires_key else 'NO',
        secret_name=secret_name, history_supported=history_supported, history_rows=int(history_rows),
        latest_date=latest_date, used_in_model='YES' if used_in_model else 'NO',
        official_endpoint=endpoint, official_format_used=fmt, detail=detail,
        market_session=market_session, region=region, data_lag_hours=str(data_lag_hours), data_type=data_type,
    )

def statuses_to_frame(items: list[ProviderStatus]) -> pd.DataFrame:
    return pd.DataFrame([asdict(x) for x in items])
