// 部署到 Zeabur 時，於前端服務的環境變數設定 VITE_API_BASE_URL
// 指向後端服務的網址（例如 https://your-backend.zeabur.app）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
