# V5.3.2 Deployment Profile

## Enabled keyed providers
- FRED
- BLS
- BEA
- EIA
- U.S. Census
- NOAA CDO
- EODHD
- Finnhub
- Alpha Vantage
- FMP Stable
- GNews
- Marketaux
- Mediastack
- New York Times (`NYTIMES_API_KEY`)
- OpenAQ v3
- J-Quants v2 (`x-api-key`)
- Telegram

## Enabled public/no-key providers
- U.S. Treasury Fiscal Data
- CFTC COT
- TWSE
- TDCC
- BOJ
- IMF
- OECD SDMX
- World Bank
- DBnomics
- Eurostat
- GDELT
- UN Comtrade
- Wikimedia Pageviews

## Disabled by design
Providers needing unconfigured or unsuitable paid credentials remain in separate modules for future activation, but are disabled in YAML and do not affect daily completeness or Telegram diagnostics.
