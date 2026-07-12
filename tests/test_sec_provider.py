from datetime import date

from pios.providers.base import ProviderContext
from pios.providers.health.sec import SecProvider


def test_sec_missing_user_agent_is_explicit(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    provider = SecProvider({"id": "sec", "type": "sec", "enabled": True})
    context = ProviderContext(
        today=date(2026, 7, 12),
        start=date(2026, 1, 14),
        config={},
    )
    _, statuses = provider.fetch(context)
    assert statuses[0].status == "MISSING_CONFIGURATION"
    assert statuses[0].secret_name == "SEC_USER_AGENT"
