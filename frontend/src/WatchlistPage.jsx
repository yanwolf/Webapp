import React, { useCallback, useEffect, useState } from 'react';
import api from './api';
import TelegramLink from './components/TelegramLink';
import WatchlistForm from './components/WatchlistForm';
import WatchlistTable from './components/WatchlistTable';

export default function WatchlistPage() {
  const [items, setItems] = useState([]);
  const [loaded, setLoaded] = useState(false);

  const fetchItems = useCallback(async () => {
    try {
      const { data } = await api.get('/api/watchlist');
      setItems(data.items || []);
    } catch (e) {
      // 靜默失敗，避免背景輪詢時一直彈錯誤
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    fetchItems();
    const timer = setInterval(fetchItems, 20000);
    return () => clearInterval(timer);
  }, [fetchItems]);

  return (
    <div>
      <p className="hero-sub" style={{ marginLeft: 0 }}>
        設定好的標的會由背景排程依K線週期自動檢查，出現新的進場/出場訊號時透過 Telegram 通知你。
      </p>

      <TelegramLink />
      <WatchlistForm onAdded={fetchItems} />
      {loaded && <WatchlistTable items={items} onChanged={fetchItems} />}

      <footer className="note">
        背景排程每 5 分鐘 tick 一次，依各標的K線週期換算實際檢查頻率（日K約每天檢查一次，1小時K約每小時一次，以此類推）。
        每個人使用自己申請的 Telegram Bot，彼此的追蹤清單跟通知互不影響。
        券商 API 自動下單尚未開通，目前僅提供通知。
      </footer>
    </div>
  );
}
