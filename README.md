# PIOS Market State Engine V6.6.1 Standalone

這是資金流主雷達的獨立市場狀態引擎，不包含宏觀雷達、新聞雷達或三雷達融合。

## V6.6 完整功能

- 官方資料 Provider 與 180 天資金流資料層
- Risk Score：五大模組風險分數
- Risk Velocity：3D／5D／10D 每日速度與加速度
- Risk Accumulation：結合百分位、廣度、持續性與速度的累積度
- Persistence Trend：≥15／25／35 分持續天數、連升天數與不下降天數
- Breadth：五大模組同步惡化比例及各模組明細
- State Machine：NORMAL → ROTATION → RISK_OFF → CREDIT_STRESS → LIQUIDITY_STRESS → SYSTEMIC
- Hysteresis：狀態升降級需連續確認，避免單日反覆切換
- State Reasons：清楚列出已確認證據、尚未升級原因及遲滯判斷
- OS 3.1.1：由狀態、持續性、廣度與可信度共同控制 452／514／433
- Historical Analog Phase：比對 2000、2008、2011、2015、2018、2020、2022，定位至約 Day N
- Historical Next Stage：依參考事件後續 10 日，顯示風險可能惡化、改善或高檔震盪，以及主要變化模組
- 180 天事件時間軸與 Telegram 每日摘要

## 首次部署

1. 設定既有 19 個 GitHub Secrets。
2. 上傳完整專案。
3. 第一次手動執行 Actions 時，將 `rebuild_analog_library` 勾選。
4. 第一次重建會建立 Analog Library v2，含完整歷史軌跡、每日構成與階段定位資料。
5. 之後每日台北時間 17:18 自動執行，不需每天重建類比庫。

若個別 API 方案不提供早期行情，該事件會記錄覆蓋率；低覆蓋事件不會硬湊相似度。

## 主要輸出

- `data/capital_flow_timeseries_180d.csv`
- `data/risk_state_history_180d.csv`
- `data/market_state_history_180d.csv`
- `data/factor_analysis.csv`
- `data/source_status.csv`
- `data/decision.json`
- `data/analog_library.json`

## V6.6.1：時區、價格輪動與跨市場傳導

本版將「最近交易時段」與 5D／20D／60D 結構分開，避免把昨夜美股、今日亞洲與中期趨勢混成同一層。輪動箭頭正式改名為「相對價格輪動代理」，並依 1D、5D、20D 一致性、強度與資料新鮮度標示為推測、初步確認或高度確認；在沒有 ETF 申購贖回或其他真實流量資料時，不宣稱資金已直接搬家。

新增亞洲本地交易所價格層、資料日期／交易時段／落後時數、跨市場傳導 0–4 階段，以及 `AGGRESSIVE_ROTATION`（劇烈板塊輪動）。亞洲本地代碼是否可讀取取決於既有市場資料方案；不支援時會在 `data/source_status.csv` 清楚標示，不會用美國掛牌 ETF 冒充今日亞洲現貨。
