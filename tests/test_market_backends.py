from pathlib import Path
import yaml
from pios.providers.market_backends.registry import discover_backends,backend_names

def test_market_backend_chain_registered():
    discover_backends()
    order=(yaml.safe_load(Path('config/market_backends.yaml').read_text()) or {}).get('order',[])
    assert order == ['eodhd','fmp','alphavantage']
    assert set(order) <= set(backend_names())
