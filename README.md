# LINE AI Assistant

LINE 台指期、全球市場、ETF、風險管理、新聞與 AI 市場懶人包機器人。

## V4.1.0 功能

### 今日市場懶人包

- `今天`、`今日`、`懶人包`：整合台股、美股、美元、三大新聞與 AI 市場重點。
- 沒有設定 OpenAI API Key 時，會自動使用本機規則產生簡短分析，Bot 仍可正常運作。

### 市場新聞

- `新聞`、`市場新聞`、`財經新聞`：顯示最新五則市場新聞。
- 新聞來源使用 Google News 公開 RSS，快取 5 分鐘；抓取失敗時可使用 30 分鐘內舊快取。

### 原有功能

- `市場`：台指期、加權、台積電、0050、道瓊、S&P 500、NASDAQ、費半、TSM ADR、美元／台幣。
- `台股`、`美股`、`ETF`、`美元`。
- 可直接輸入 `0050`、`0056`、`00919`、`00940`、`台積電`、`費半` 等查詢單一行情。
- `停損50 10口 小台`、`風險3000 停損50`、`本金20萬 風險2% 停損50 小台`。

## 環境變數

```env
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token

# 選填：未設定時會使用本機規則摘要
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini

# 選填：Google News RSS 搜尋條件
NEWS_QUERY=台股 OR 台積電 OR 美股 OR 聯準會 OR 半導體 when:1d
```

OpenAI 串接使用官方 Python SDK 的 Responses API。AI 分析設有 5 分鐘記憶體快取，避免短時間重複呼叫。

## 專案架構

```text
commands/
  today.py          今天市場懶人包
  news.py           新聞指令格式
  global_market.py  全球市場指令
  stoploss.py       風險管理指令
services/
  ai.py             OpenAI 與本機備援分析
  news.py           Google News RSS 與快取
  global_market.py  全球行情與快取
bot/                LINE Webhook 與回覆
config.py           環境變數與常數
main.py             FastAPI 路由入口
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

> 免費行情可能延遲；新聞與 AI 摘要僅供資訊整理，不構成投資建議。
