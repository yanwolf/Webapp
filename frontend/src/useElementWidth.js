import { useEffect, useState } from 'react';

/**
 * 用來強迫 Recharts 的 ResponsiveContainer 在版面穩定後重新量測一次。
 * 做法：回傳一個會變動的數字（remeasureKey），把它當成 ResponsiveContainer 的 key，
 * 每次數字變動就會強迫該元件整個重新掛載，逼 Recharts 用當下最新的容器尺寸重新計算，
 * 避免它卡在第一次渲染時量到的（可能不準確的）舊尺寸。
 *
 * 觸發時機：
 *   - 掛載後 200ms / 600ms / 1200ms 各補量一次（涵蓋字型載入、版面延遲穩定等情況）
 *   - 視窗尺寸改變 / 螢幕旋轉時
 */
export function useRemeasureKey() {
  const [key, setKey] = useState(0);

  useEffect(() => {
    const bump = () => setKey((k) => k + 1);

    const timers = [setTimeout(bump, 200), setTimeout(bump, 600), setTimeout(bump, 1200)];

    window.addEventListener('resize', bump);
    window.addEventListener('orientationchange', bump);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', bump);
    }

    return () => {
      timers.forEach(clearTimeout);
      window.removeEventListener('resize', bump);
      window.removeEventListener('orientationchange', bump);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', bump);
      }
    };
  }, []);

  return key;
}
