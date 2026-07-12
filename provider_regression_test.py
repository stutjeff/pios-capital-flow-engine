from pathlib import Path
import yaml
from pios.providers.registry import discover,names

discover()
registered=set(names())
cfg=yaml.safe_load(Path('config/providers.yaml').read_text()) or {}
configured={x['type'] for x in cfg.get('providers',[])} | {'market_chain'}
missing=configured-registered
assert not missing, f'Missing provider registrations: {sorted(missing)}'
assert 'diagnostics' not in registered, 'Legacy aggregated diagnostics provider must not exist.'
for f in ('config/providers.yaml','config/sectors.yaml','config/scoring.yaml','.github/workflows/pios-capital-flow-engine.yml'):
    assert Path(f).exists(), f'Missing required file: {f}'
    if f.endswith(('.yaml','.yml')): yaml.safe_load(Path(f).read_text())
print(f'Provider registry passed: {len(registered)} provider types; all configured types registered.')
