# LINE AI Assistant

LINE 台指期行情與風險管理機器人。

## V4.0.2 功能

- `台指`、`台指期`：查詢台指期近一行情。
- `停損50`：微台 1 口，試算停損位置與金額。
- `停損50 10口 小台`：指定商品與口數。
- `停損80 3口 大台`：支援大台。
- `風險3000 停損50`：依最大虧損反算微台、小台、大台可下口數。
- `風險5000 停損30 小台`：指定商品反算口數。
- `本金20萬 風險2% 停損50 小台`：依本金與風險比例反算口數。
- Yahoo 行情失敗時，自動改用 GAS／期交所每日資料備援。

## 商品點值

| 商品 | 代碼 | 每點價值 |
|---|---|---:|
| 微型臺指期貨 | TMF | NT$10 |
| 小型臺指期貨 | MTX | NT$50 |
| 臺股期貨（大台） | TX | NT$200 |

## 專案架構

```text
commands/   指令解析與訊息格式
services/   行情、數字處理與 Risk Manager
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

> 風險試算不含手續費、交易稅與滑價，不構成投資建議。
