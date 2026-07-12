# Clean rebuild deployment

This release must be uploaded to a new, empty GitHub repository or to a repository whose root has been cleared first.

The repository root should contain only:

- `.github/`
- `config/`
- `data/`
- `pios/`
- `templates/`
- `tests/`
- `main.py`
- `provider_regression_test.py`
- `repository_sanity_check.py`
- `requirements.txt`
- documentation files

Do not leave these legacy root modules in the repository:

`engine.py`, `history.py`, `http.py`, `models.py`, `report.py`, `scoring.py`, `telegram.py`, `providers.py`, `official_providers.py`, `capital_flow_engine.py`, `provider_health.py`.

GitHub Actions runs `repository_sanity_check.py` before tests. If legacy root files reappear, the workflow will stop with an explicit list instead of failing later inside urllib3 or imports.
