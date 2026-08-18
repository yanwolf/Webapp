/**
 * 圖表顯示用的資料精簡（不影響底層績效計算，只影響畫面畫幾個點）
 * ============================================================
 * 手機瀏覽器畫幾千個資料點的SVG折線圖時容易處理不完、畫到一半就卡住，
 * 尤其是小時K/分K這種資料量大的週期。畫面上本來就看不出上千個點的差異，
 * 所以超過門檻時用固定間隔抽稀；keepIndices 用來確保重要的點（例如進出場K棒）
 * 一定會被保留，不會因為抽稀被跳過。
 */
export function downsampleForChart(rows, maxPoints = 600, keepIndices = []) {
  if (!rows || rows.length <= maxPoints) return rows || [];
  const keepSet = new Set(keepIndices);
  const stride = Math.ceil(rows.length / maxPoints);
  const result = [];
  for (let i = 0; i < rows.length; i++) {
    if (i % stride === 0 || keepSet.has(i) || i === rows.length - 1) {
      result.push(rows[i]);
    }
  }
  return result;
}
