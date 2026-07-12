from pathlib import Path
import yaml
from pios.providers.registry import discover,names

def test_every_configured_provider_is_registered():
    discover(); registered=set(names())
    cfg=yaml.safe_load(Path('config/providers.yaml').read_text()) or {}
    configured={x['type'] for x in cfg.get('providers',[])} | {'market_chain'}
    assert configured <= registered
    assert 'diagnostics' not in registered

def test_provider_count_is_fully_modular():
    discover(); assert len(names()) >= 40
