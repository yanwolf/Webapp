import React, { useEffect, useRef } from 'react';

/**
 * TradingView 官方免費的嵌入式即時走勢圖（不用API金鑰，資料直接來自TradingView自己的伺服器）
 * 這張圖是TradingView自己的原始報價，跟我們自己畫的策略圖（疊了均線/進出場箭頭）是分開的兩回事，
 * 這裡只是提供一個額外的、跟大盤即時同步的參考視角。
 */
export default function TradingViewMiniWidget({ symbol, height = 220 }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !symbol) return undefined;
    container.innerHTML = '';

    const widgetDiv = document.createElement('div');
    widgetDiv.className = 'tradingview-widget-container__widget';
    container.appendChild(widgetDiv);

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js';
    script.async = true;
    script.innerHTML = JSON.stringify({
      symbol,
      width: '100%',
      height,
      locale: 'zh_TW',
      dateRange: '1D',
      colorTheme: 'dark',
      isTransparent: true,
      autosize: false,
    });
    container.appendChild(script);

    return () => { container.innerHTML = ''; };
  }, [symbol, height]);

  return <div className="tradingview-widget-container" ref={containerRef} style={{ height, marginTop: 12 }} />;
}
