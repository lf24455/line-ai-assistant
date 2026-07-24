# Changelog

## V4.0.2 - 2026-07-24

- 新增 Risk Manager。
- 停損試算支援微台（TMF）、小台（MTX）及大台（TX）。
- 新增自然語言格式，例如 `50點 小台10口`。
- 新增最大風險反算口數，例如 `風險3000 停損50`。
- 新增本金與風險比例試算，例如 `本金20萬 風險2% 停損50 小台`。
- 新增輸入驗證與友善錯誤提示。

## V4.0.1 - 2026-07-24

- 將原本單一 `main.py` 拆成 `commands`、`services`、`bot` 模組。
- 保留原有 LINE Webhook、台指查詢、停損試算及 Yahoo／TAIFEX 備援功能。
- 保留 Render 啟動方式 `uvicorn main:app`，部署設定不需更改。
- 新增 `.gitignore`。
