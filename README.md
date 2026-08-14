# 黑鑽布林策略回測（網站版）

依教學影片重點整理實作的布林通道完整策略，改寫成 FastAPI + React/Vite 的網站版本，
可輸入美股、台股、加密貨幣代碼即時回測。架構與你現有的 黑鑽選股 / crypto screener 一致，
可直接部署到 Zeabur。

```
webapp/
├── backend/          FastAPI 服務（抓資料、跑策略、回傳 JSON）
│   ├── main.py
│   ├── bollinger_strategy.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/         React + Vite 前端（暗色系「黑鑽」風格 UI）
    ├── src/
    └── Dockerfile
```

## 本機測試

**後端**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**前端**
```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```
瀏覽器開 http://localhost:5173

## 部署到 Zeabur

在同一個 Zeabur Project 裡建立**兩個服務**（monorepo，各自指到子資料夾）：

### 1. 後端服務 (backend)
- Root Directory 設為 `backend`
- Zeabur 會偵測到 `Dockerfile` 直接建置
- 部署後會拿到一組網域，例如 `https://bollinger-backend.zeabur.app`
- 不需要額外環境變數（PORT 由 Zeabur 自動注入）

### 2. 前端服務 (frontend)
- Root Directory 設為 `frontend`
- 在服務的 **Environment Variables** 加入：
  ```
  VITE_API_BASE_URL=https://bollinger-backend.zeabur.app
  ```
  （換成你後端服務實際的網域，注意這是「建置時」變數，設定完要重新 Deploy 一次才會生效）
- Zeabur 會用附帶的 `Dockerfile` 建置並用 `serve` 提供靜態檔案

### 3.（可選）自訂網域 / CORS
- 如果想收緊 CORS，把 `backend/main.py` 裡 `allow_origins=["*"]` 改成你前端的正式網域。

## 功能對照

| 前端輸入 | 後端行為 |
|---|---|
| 市場＝台股，代碼＝2330 | 自動組成 `2330.TW` 丟給 yfinance |
| 市場＝加密貨幣，代碼＝BTC | 自動組成 `BTC-USD` |
| 市場＝美股，代碼＝AAPL | 原樣查詢 |

策略邏輯（擠壓突破／貼軌趨勢跟隨／W底 M頭背離確認）與先前提供的獨立回測腳本完全相同，
細節與可調參數說明請見 `backend/bollinger_strategy.py` 內的註解。

## 已知限制
- yfinance 的加密貨幣資料（如 BTC-USD）通常只有幾年歷史，太早的起始日期會抓不到資料。
- 台股 ETF/個股偶爾會有 yfinance 資料延遲或缺漏，回測結果僅供參考。
- 目前是單一部位（同時間只持有一筆多單或空單），尚未支援多標的組合回測。
