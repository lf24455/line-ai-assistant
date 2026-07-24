# LINE AI Assistant

LINE 台指期查詢與微型臺指停損試算機器人。

## 目前功能

- `台指`、`台指期`：查詢台指期近一行情。
- `停損50`：以目前價格試算 50 點停損，預設 1 口。
- `停損50 10口`：指定停損點數與口數。
- `說明`、`功能`、`指令`、`help`：顯示指令說明。
- Yahoo 行情失敗時，自動改用 GAS／期交所每日資料備援。

## 專案架構

```text
commands/   指令解析與訊息格式
services/   Yahoo、TAIFEX、數字處理與行情來源
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

本專案保留以下啟動指令：

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
