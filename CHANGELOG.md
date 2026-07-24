# Changelog

## V4.0.1 - 2026-07-24

- 將原本單一 `main.py` 拆成 `commands`、`services`、`linebot` 模組。
- 保留原有 LINE Webhook、台指查詢、停損試算及 Yahoo／TAIFEX 備援功能。
- 保留 Render 啟動方式 `uvicorn main:app`，部署設定不需更改。
- 新增 `.gitignore`。
