# GitHub Secrets — V5.3.2

Create these **Repository secrets** exactly as written.

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

FRED_API_KEY
BLS_API_KEY
BEA_API_KEY
EIA_API_KEY
CENSUS_API_KEY
NOAA_CDO_TOKEN
SEC_USER_AGENT

EODHD_API_KEY
FINNHUB_API_KEY
ALPHAVANTAGE_API_KEY
FMP_API_KEY

GNEWS_API_KEY
MARKETAUX_API_KEY
MEDIASTACK_API_KEY
NYTIMES_API_KEY

OPENAQ_API_KEY
JQUANTS_API_KEY
```

No J-Quants email or password is used. V5.3.2 uses the J-Quants v2 API key through the `x-api-key` header.

The following providers remain modular in the codebase but are disabled in `config/providers.yaml` because their keys are not part of this deployment, their free dedicated API access is unsuitable, or they require separate compliance configuration:

```text
NewsAPI
The Guardian
SerpApi
OpenFIGI
OpenCorporates
OpenSanctions
NASA
Trading Economics
EDINET
Fubon SDK
```

## SEC EDGAR

`SEC_USER_AGENT` is not an API key. Use a descriptive value such as `PIOS Capital Flow Engine contact@example.com`.
