# PIOS Capital Flow Engine V5.3.2 — Fully Modular, Deployment-Aligned

This release removes the final aggregated provider module. Every API/source now has its own provider module, while shared transport, error classification, history, scoring, reporting, and Telegram logic stay in the core.

## Architecture

```text
main.py
config/
  providers.yaml
  market_backends.yaml
  sectors.yaml
  scoring.yaml
pios/
  core/
    engine.py
    history.py
    scoring.py
    report.py
    telegram.py
    http.py
    models.py
  providers/
    fred.py
    eia.py
    treasury.py
    cftc.py
    market.py                 # chain orchestrator only
    market_backends/
      eodhd.py
      fmp.py
      alphavantage.py
    health/
      twse.py
      tdcc.py
      bls.py
      bea.py
      census.py
      sec.py
      jquants.py
      edinet.py
      boj.py
      imf.py
      oecd.py
      worldbank.py
      dbnomics.py
      eurostat.py
      finnhub.py
      gnews.py
      newsapi.py
      marketaux.py
      guardian.py
      nyt.py
      gdelt.py
      serpapi.py
      mediastack.py
      openfigi.py
      uncomtrade.py
      opencorporates.py
      opensanctions.py
      openaq.py
      noaa.py
      nasa.py
      wikimedia.py
      tradingeconomics.py
      nasdaq_datalink.py
      stooq.py
      fubon.py
```

## Adding a new data source

1. Add one new module under `pios/providers/health/` for a diagnostic/snapshot source, or under `pios/providers/market_backends/` for a historical market-price backend.
2. Register it with `@register("name")` or `@register_backend("name")`.
3. Add one entry to `config/providers.yaml` or `config/market_backends.yaml`.
4. Add a model factor only when needed in `config/scoring.yaml` or `config/sectors.yaml`.

The engine, history database, Telegram report, and GitHub workflow do not need to be rewritten.

## Runtime behavior

- Scheduled daily at 17:18 Asia/Taipei (`09:18 UTC`).
- First run backfills available history from each historical provider.
- Rolling history keeps the latest 180 calendar days.
- Market chain: EODHD → FMP Stable → Alpha Vantage Compact.
- Nasdaq Data Link is intentionally not called daily.
- Stooq is disabled because it does not provide an official documented API contract.
- Every source writes an independent row to `data/source_status.csv`.
- Telegram shows decision-relevant failures only; full diagnostics stay in CSV.

## Validation included

- Python compile/import tests.
- Every configured provider type must be registered.
- Legacy aggregated `diagnostics` provider must not be registered.
- Market backend chain registration test.
- HTTP error classification test.
- Scoring tests.

## Deployment

Upload the entire extracted repository. The included workflow is:

```text
.github/workflows/pios-capital-flow-engine.yml
```

Enable GitHub Actions read/write permissions so generated data can be committed.


## V5.3.2 deployment profile

The GitHub workflow now references only the 18 secrets actually configured by the user. Providers that require other paid or unavailable credentials are disabled in `config/providers.yaml`, so they do not generate daily `MISSING_KEY` noise. Public no-key providers remain enabled.

The New York Times secret name is standardized as `NYTIMES_API_KEY`. J-Quants uses only `JQUANTS_API_KEY`; email/password authentication is not used.


## V5.3 新增
- 資金流向地圖：配對主要流出與流入板塊，顯示20日相對差與歷史強度。
- 歷史強度：5/20/60/120日變化均可計算180日絕對強度百分位，Telegram顯示20日星級。
- OS切換進度：顯示距離514與433仍差的風險分數、可信度與進度百分比。
- 180日事件時間軸：顯示異常起始日、持續天數、擴大或消退、事件頻率與近期日期。
