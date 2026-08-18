/**
 * 日期字串 <-> 數字時間戳的轉換工具
 * ====================================
 * 原本X軸用「日期文字」當類別軸（category axis），Recharts 處理大量文字類別時
 * 定位資料點的邏輯在部分行動裝置瀏覽器上會出問題，導致資料被擠壓在一小塊區域。
 * 改用「數字時間戳」當數值軸（number axis）能完全避開這整類問題，
 * 是 Recharts 官方畫時間序列圖表建議的標準做法。
 */
export function toTs(dateStr) {
  if (!dateStr) return null;
  const iso = dateStr.includes(' ') ? dateStr.replace(' ', 'T') : dateStr;
  const t = new Date(iso).getTime();
  return Number.isNaN(t) ? null : t;
}

export function formatTick(ts, hasTime) {
  const d = new Date(ts);
  const pad = (n) => String(n).padStart(2, '0');
  if (hasTime) {
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
