import React from 'react';

const STRATEGY_INTRO = [
  { name: '布林通道策略', desc: '擠壓後放量突破、貼軌趨勢跟隨、W底/M頭背離確認，適合有明顯波動循環的行情。' },
  { name: '均線三刀流', desc: 'EMA快/中/慢三線排列判斷多空、黃金死亡交叉進出場，適合趨勢明確的行情。' },
  { name: '均線黃金/死亡交叉', desc: '三刀流的簡化版，雙均線交叉，訊號較少但邏輯單純。' },
  { name: '唐奇安通道突破', desc: 'N日高低點突破進場（海龜交易法則），適合大波段趨勢行情。' },
  { name: 'RSI 超買超賣', desc: '跌深反彈、漲多拉回，均值回歸邏輯，適合區間震盪、無明顯趨勢的行情。' },
  { name: 'MACD 動量策略', desc: 'MACD與訊號線交叉，捕捉中期動能轉折。' },
  { name: '買進持有（基準）', desc: '單純買進抱著不動，用來檢驗其他策略是不是真的有比較厲害。' },
];

export default function HomePage({ onNavigate }) {
  return (
    <div>
      <div className="panel" style={{ marginBottom: 24 }}>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.8, margin: 0 }}>
          這個網站可以用歷史資料回測多種技術分析策略在<b style={{ color: 'var(--text)' }}>美股、台股、加密貨幣</b>上的表現，
          找到你喜歡的策略後，還能設定<b style={{ color: 'var(--text)' }}>追蹤清單</b>，透過 Telegram 自動通知進出場時機。
        </p>
      </div>

      <div className="chart-panel">
        <div className="chart-panel-title">三步驟快速上手</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>

          <div style={{ display: 'flex', gap: 14 }}>
            <div className="step-num">1</div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>先跑一次單一策略回測</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13.5, lineHeight: 1.7 }}>
                去「回測」頁籤，輸入一檔你感興趣的標的（打股票名稱就能搜尋代號），挑一個策略，看看過去幾年的歷史績效如何。
              </div>
              <button className="link-btn" onClick={() => onNavigate('backtest')}>前往回測 →</button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 14 }}>
            <div className="step-num">2</div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>比較所有策略，找出打贏大盤的</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13.5, lineHeight: 1.7 }}>
                同一檔標的，不同策略績效常常差很多。去「策略比較」頁籤，選好交易風格（短沖/長線波段），
                一次跑完全部策略並排名，清楚看到哪個策略真的贏過「買進持有」。
              </div>
              <button className="link-btn" onClick={() => onNavigate('compare')}>前往策略比較 →</button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 14 }}>
            <div className="step-num">3</div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>設定追蹤，讓系統自動幫你盯盤</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13.5, lineHeight: 1.7 }}>
                找到喜歡的策略組合後，去「追蹤清單」頁籤設定你自己的 Telegram Bot（頁面裡有教學），
                之後出現新的進場/出場訊號，系統會自動傳訊息通知你，不用一直盯盤。
              </div>
              <button className="link-btn" onClick={() => onNavigate('watchlist')}>前往追蹤清單 →</button>
            </div>
          </div>

        </div>
      </div>

      <div className="chart-panel">
        <div className="chart-panel-title">策略小百科</div>
        <div className="table-wrap" style={{ marginTop: 8 }}>
          <table className="trades">
            <tbody>
              {STRATEGY_INTRO.map((s) => (
                <tr key={s.name}>
                  <td style={{ textAlign: 'left', fontWeight: 600, whiteSpace: 'nowrap', verticalAlign: 'top', paddingRight: 16 }}>
                    {s.name}
                  </td>
                  <td style={{ textAlign: 'left', color: 'var(--text-muted)', fontFamily: 'var(--font-ui)', fontWeight: 400 }}>
                    {s.desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel">
        <div className="chart-panel-title">常見名詞</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 3 }}>現股買賣 / 現股+做空</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
              「現股買賣」只做多（買進、等漲、賣出），跟一般股票戶頭的現股交易一樣。「現股+做空」則會在策略判斷偏空時也嘗試放空，
              需要你的券商帳戶支援融券或期貨等放空工具才能實際跟著操作。
            </div>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 3 }}>K線週期怎麼選</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
              短沖建議用 1小時K 或更短（資料回溯天數較短，樣本較少）；長線波段建議用日K（資料最完整，統計上最可信）。
            </div>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 3 }}>資料來源</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.7 }}>
              台股日K優先用 FinMind，美股優先用 Twelve Data，加密貨幣優先用 Binance；
              沒設定對應金鑰、或暫時抓取失敗時，會自動退回 Yahoo Finance，不會讓回測失敗。
              每次回測結果下方會標示實際用了哪個資料來源。
            </div>
          </div>
        </div>
      </div>

      <div className="info-box">
        ⚠️ 這個網站所有策略績效都是歷史回測結果，不代表未來表現，也不構成投資建議。實際操作前請自行評估風險。
      </div>
    </div>
  );
}
