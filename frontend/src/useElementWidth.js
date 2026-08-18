import { useEffect, useRef, useState } from 'react';

/**
 * 自己量容器實際寬度（用 ResizeObserver），不依賴 Recharts 的 ResponsiveContainer 自動偵測。
 * 部分行動裝置瀏覽器在版面剛渲染、還沒穩定時量到的寬度不準，
 * ResponsiveContainer 之後又沒有正確重新量測，導致圖表被鎖定在錯誤的寬度上。
 * 回傳 [ref, width]，把 ref 掛在外層 div 上，width 是該 div 目前的實際像素寬度。
 */
export function useElementWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;

    const update = () => {
      const w = el.clientWidth;
      if (w > 0) setWidth(w);
    };

    update();

    const ro = new ResizeObserver(() => update());
    ro.observe(el);
    window.addEventListener('orientationchange', update);
    window.addEventListener('resize', update);

    return () => {
      ro.disconnect();
      window.removeEventListener('orientationchange', update);
      window.removeEventListener('resize', update);
    };
  }, []);

  return [ref, width];
}
