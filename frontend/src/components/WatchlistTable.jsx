import React from 'react';
import api from '../api';

const MARKET_LABELS = { us: '美股', tw: '台股', crypto: '加密貨幣' };

function timeAgo(iso) {
  if (!iso) return '尚未檢查';
  const diffMs = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return '剛剛';
  if (min < 60) return `${min}分鐘前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}小時前`;
  return `${Math.floor(hr / 24)}天前`;
}

function pct(v) {
  if (v == null) return '';
  const s = (v * 100).toFixed(2);
  return ` ${v >= 0 ? '+' : ''}${s}%`;
}

function PositionCell({ item }) {
  const pos = item.open_position;
  if (pos) {
    const isLong = pos.side === 'long';
    return (
      <div>
        <span className={`side-tag ${isLong ? 'long' : 'short'}`} style={{ fontSize: 11 }}>
          {isLong ? '目前持有多單' : '目前持有空單'}
        </span>
        <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 3 }}>
          {pos.entry_date} 進場 @ {pos.entry_price?.toFixed(2)}
          <span className={pos.unrealized_return >= 0 ? 'up' : 'down'}>{pct(pos.unrealized_return)}</span>
        </div>
      </div>
    );
  }
  return <span style={{ color: 'var(--text-muted)' }}>{item.last_event_summary || '目前空手'}</span>;
}

export default function WatchlistTable({ items, onChanged }) {
  const toggle = async (id, enabled) => {
    await api.patch(`/api/watchlist/${id}`, null, { params: { enabled: !enabled } });
    onChanged && onChanged();
  };

  const remove = async (id) => {
    await api.delete(`/api/watchlist/${id}`);
    onChanged && onChanged();
  };

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        追蹤清單 <span className="badge">共 {items.length} 檔</span>
      </div>
      {items.length === 0 ? (
        <div className="empty-state" style={{ marginTop: 8 }}>還沒有追蹤任何標的，上面新增一個吧</div>
      ) : (
        <div className="table-wrap">
          <table className="trades">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>標的</th>
                <th style={{ textAlign: 'left' }}>策略</th>
                <th style={{ textAlign: 'left' }}>週期</th>
                <th style={{ textAlign: 'left' }}>上次檢查</th>
                <th style={{ textAlign: 'left' }}>目前狀態</th>
                <th>狀態</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td style={{ textAlign: 'left' }}>{it.ticker}<span style={{ color: 'var(--text-faint)', fontSize: 11 }}> {MARKET_LABELS[it.market]}</span></td>
                  <td style={{ textAlign: 'left' }}>{it.strategy_label}</td>
                  <td style={{ textAlign: 'left' }}>{it.interval}</td>
                  <td style={{ textAlign: 'left', color: 'var(--text-faint)' }}>{timeAgo(it.last_checked_at)}</td>
                  <td style={{ textAlign: 'left' }}><PositionCell item={it} /></td>
                  <td>
                    <span className={`side-tag ${it.enabled ? 'long' : 'short'}`}>
                      {it.enabled ? '追蹤中' : '已暫停'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => toggle(it.id, it.enabled)}
                      style={{ background: 'none', border: 'none', color: 'var(--cyan)', cursor: 'pointer', fontSize: 12, marginRight: 10 }}
                    >
                      {it.enabled ? '暫停' : '啟用'}
                    </button>
                    <button
                      onClick={() => remove(it.id)}
                      style={{ background: 'none', border: 'none', color: 'var(--up)', cursor: 'pointer', fontSize: 12 }}
                    >
                      刪除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
