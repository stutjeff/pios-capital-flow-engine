# PIOS API Master — V5.3.2 Clean Modular

Every active or intentionally disabled source has an independent adapter module. No source is hidden inside a combined diagnostics function.

## Historical/model sources

| Source | Module | Role | History |
|---|---|---|---|
| FRED | `pios/providers/fred.py` | rates, spreads, dollar, VIX | full range requested |
| EIA API v2 | `pios/providers/eia.py` | WTI spot | full range requested |
| U.S. Treasury Fiscal Data | `pios/providers/treasury.py` | average Treasury rates | full range requested |
| CFTC TFF annual ZIP | `pios/providers/cftc.py` | asset-manager positioning | weekly history |
| EODHD | `market_backends/eodhd.py` | primary ETF history | requested range |
| FMP Stable | `market_backends/fmp.py` | first market fallback | requested range/plan |
| Alpha Vantage | `market_backends/alphavantage.py` | second market fallback | compact, latest ~100 rows |

## Independent official/public diagnostic sources

TWSE, TDCC, BLS, BEA, Census, SEC EDGAR, J-Quants V2, EDINET v2, BOJ, IMF DataMapper, OECD SDMX, World Bank v2, DBnomics, Eurostat, Finnhub, GNews, NewsAPI, Marketaux, Guardian, NYT, GDELT, SerpApi, Mediastack, OpenFIGI, UN Comtrade, OpenCorporates, OpenSanctions, OpenAQ v3, NOAA CDO v2, NASA, Wikimedia Pageviews, Trading Economics, and the optional Fubon Neo SDK.

Each appears as one module under `pios/providers/health/` and one row in `source_status.csv`.

## Disabled by design

- Nasdaq Data Link: no daily call; relevant datasets are plan/institution dependent.
- Stooq: no active call; no official documented API contract.

## Configuration boundaries

- `config/providers.yaml`: provider instances and enable/disable flags.
- `config/market_backends.yaml`: market fallback order.
- `config/sectors.yaml`: symbols and factor column names.
- `config/scoring.yaml`: model factor list, rolling window, and mode thresholds.

## V5.3.2 deployment alignment

The active GitHub deployment uses only the following keyed sources: FRED, BLS, BEA, EIA, Census, NOAA, EODHD, Finnhub, Alpha Vantage, FMP, GNews, Marketaux, Mediastack, New York Times, OpenAQ, and J-Quants, plus Telegram delivery. Providers requiring other credentials are retained as modular code but disabled in `config/providers.yaml`.
