# V6 Deployment Profile

- Entry point: `main.py`
- Daily schedule: 17:18 Asia/Taipei (09:18 UTC)
- Python: 3.12
- Secrets: same 19 as V5.3.2; no new secret
- First manual run: set `rebuild_analog_library=true`
- Rolling windows: market data 180 calendar days; risk/state histories 180 observations maximum
- External radar fusion: optional JSON snapshots under `data/external/`
