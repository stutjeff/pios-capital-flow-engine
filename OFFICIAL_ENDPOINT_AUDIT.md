# Official Endpoint Audit — V5.3.2

Every adapter writes `official_endpoint` and `official_format_used` to `data/source_status.csv`. Endpoint changes are isolated to that source's module.

## Core historical endpoints

| Source | Endpoint / format |
|---|---|
| FRED | `https://api.stlouisfed.org/fred/series/observations` with `series_id`, `api_key`, `file_type=json`, observation dates |
| EIA | `https://api.eia.gov/v2/petroleum/pri/spt/data/` with API v2 facets, frequency, start/end, sorting |
| EODHD | `/api/eod/{symbol}.US` with `api_token`, `fmt=json`, `from`, `to`, `period=d`, `order=a` |
| FMP | `/stable/historical-price-eod/full` with `symbol`, `from`, `to`, `apikey` |
| Alpha Vantage | `/query` with `TIME_SERIES_DAILY`, `outputsize=compact` |
| Treasury Fiscal Data | `/services/api/fiscal_service/v2/accounting/od/avg_interest_rates` |
| CFTC | official annual `fut_fin_txt_{year}.zip` Traders in Financial Futures file |

## Regional and official public endpoints

- TWSE OpenAPI `/v1/fund/BFI82U`
- TDCC OpenAPI `/v1/opendata/1-5`
- BLS Public Data API v2 `POST /publicAPI/v2/timeseries/data/`
- BEA API `https://apps.bea.gov/api/data`
- Census Data API ACS profile endpoint
- SEC EDGAR official company tickers endpoint with descriptive User-Agent
- J-Quants API V2 `/v2/equities/investor-types` with `x-api-key`
- EDINET API v2 `/api/v2/documents.json`
- OECD SDMX public REST v1
- World Bank API v2
- Eurostat dissemination statistics API 1.0
- OpenAQ API v3 with `X-API-Key`
- NOAA CDO API v2 with token header

## Deliberate exclusions

- No Yahoo Finance chart endpoint.
- No active Stooq call.
- No daily Nasdaq Data Link call.
- No FMP legacy `/api/v3/historical-price-full` endpoint.
- No Alpha Vantage `outputsize=full` assumption for free keys.

## V5.3.2.1 deployment note

The workflow secret surface has been reduced to the exact credentials configured by the user. Disabled providers are not called, do not affect completeness, and do not produce daily missing-key warnings. New York Times uses `NYTIMES_API_KEY`; J-Quants uses only `JQUANTS_API_KEY` with the v2 `x-api-key` header.
