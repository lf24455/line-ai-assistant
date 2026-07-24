# LINE AI Assistant

LINE 台指期、全球市場、ETF 行情與風險管理機器人。

## V4.0.3 功能

### 全球市場

- `市場`：台指期、加權、台積電、0050、道瓊、S&P 500、NASDAQ、費半、TSM ADR、美元／台幣。
- `台股`：台指期、加權、台積電、0050。
- `美股`：道瓊、S&P 500、NASDAQ、費半、TSM ADR。
- `ETF`：0050、0056、00919、00940。
- `美元`：USD/TWD。
- 可直接輸入 `0050`、`0056`、`00919`、`00940`、`台積電`、`費半` 等查詢單一行情。
- Yahoo Finance 行情採 15 秒記憶體快取；即時查詢失敗時，最多使用 10 分鐘內的成功快取。

### Risk Manager

- `停損50`：微台 1 口，試算停損位置與金額。
- `停損50 10口 小台`：指定商品與口數。
- `停損80 3口 大台`：支援大台。
- `風險3000 停損50`：依最大虧損反算可下口數。
- `本金20萬 風險2% 停損50 小台`：依本金與風險比例反算口數。

## 商品點值

| 商品 | 代碼 | 每點價值 |
|---|---|---:|
| 微型臺指期貨 | TMF | NT$10 |
| 小型臺指期貨 | MTX | NT$50 |
| 臺股期貨（大台） | TX | NT$200 |

## 專案架構

```text
commands/   指令解析與訊息格式
services/   行情、快取、數字處理與 Risk Manager
bot/        LINE Webhook 與回覆
config.py   環境變數與常數
main.py     FastAPI 路由入口
```

## 環境變數

```env
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
```

## 本機啟動

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Render

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

> Yahoo 免費行情可能延遲；風險試算不含手續費、交易稅與滑價，均不構成投資建議。
