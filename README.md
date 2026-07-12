# PIOS Market State Engine V6.0.1

V6 延續 V5.3.2 的官方資料 Provider 與 180 天資金流資料層，新增完整市場狀態分析層：

- Risk Score：既有五大模組風險分數
- Momentum：1D／3D／5D 變化與 5D／10D 斜率
- Persistence：風險高於 15／25／35 分的連續天數
- Breadth：五大模組同步惡化比例
- State Machine：NORMAL → ROTATION → RISK_OFF → CREDIT_STRESS → LIQUIDITY_STRESS → SYSTEMIC
- Hysteresis：狀態升降級需連續確認，避免單日反覆切換
- OS 3.1.1：由狀態、持續性、廣度與可信度共同控制 452／514／433
- Historical Analogs：與 2000、2008、2011、2015、2018、2020、2022 的實際資料輪廓比較
- Radar Fusion：可讀取宏觀雷達與新聞雷達最新 JSON 快照；缺少時不會假造分數

## 首次部署

1. 設定既有 19 個 GitHub Secrets。
2. 上傳完整專案。
3. 第一次手動執行 Actions 時，將 `rebuild_analog_library` 選為 `true`。
4. 之後每日台北時間 17:18 自動執行，不需每天重建歷史類比庫。

歷史類比庫的建立會使用既有 FRED 與行情 API。若個別方案不提供早期行情，該事件會記錄覆蓋率，低覆蓋事件不會被拿來湊相似度。

## 三雷達融合（未啟用）快照

可選擇放入：


最小格式：

```json
{"risk_score": 42.5, "confidence": 86.0}
```

沒有快照時，資金流主雷達照常運作，報告會誠實標示尚未接入。

## 主要輸出

- `data/capital_flow_timeseries_180d.csv`
- `data/risk_state_history_180d.csv`
- `data/market_state_history_180d.csv`
- `data/factor_analysis.csv`
- `data/source_status.csv`
- `data/decision.json`
- `data/analog_library.json`
