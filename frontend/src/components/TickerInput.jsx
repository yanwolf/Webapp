import React, { useEffect, useRef, useState } from 'react';
import api from '../api';

export default function TickerInput({ market, value, onChange, placeholder }) {
  const [query, setQuery] = useState(value || '');
  const [results, setResults] = useState([]);
  const [unavailableMsg, setUnavailableMsg] = useState(null);
  const [open, setOpen] = useState(false);
  const [hoverIdx, setHoverIdx] = useState(-1);
  const debounceRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => { setQuery(value || ''); }, [value]);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  // 換市場時清空候選清單，避免殘留上一個市場的結果
  useEffect(() => { setResults([]); setUnavailableMsg(null); }, [market]);

  const fetchResults = (q) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const { data } = await api.get('/api/search-ticker', { params: { market, query: q.trim() } });
        if (!data.available) {
          setUnavailableMsg(data.message);
          setResults([]);
        } else {
          setUnavailableMsg(null);
          setResults(data.results || []);
        }
        setOpen(true);
        setHoverIdx(-1);
      } catch (e) {
        setResults([]);
      }
    }, 300);
  };

  const handleChange = (e) => {
    const v = e.target.value;
    setQuery(v);
    onChange(v);
    fetchResults(v);
  };

  const select = (item) => {
    setQuery(item.symbol);
    onChange(item.symbol);
    setResults([]);
    setOpen(false);
  };

  const handleKeyDown = (e) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHoverIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHoverIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && hoverIdx >= 0) {
      e.preventDefault();
      select(results[hoverIdx]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={boxRef}>
      <input
        type="text"
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => (results.length || unavailableMsg) && setOpen(true)}
        placeholder={placeholder}
        autoComplete="off"
      />
      {open && (results.length > 0 || unavailableMsg) && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30,
          background: 'var(--panel-raised)', border: '1px solid var(--border)', borderRadius: 8,
          marginTop: 4, maxHeight: 260, overflowY: 'auto',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
        }}>
          {unavailableMsg ? (
            <div style={{ padding: '10px 12px', fontSize: 12, color: 'var(--text-faint)' }}>{unavailableMsg}</div>
          ) : (
            results.map((r, i) => (
              <div
                key={r.symbol + i}
                onMouseDown={(e) => { e.preventDefault(); select(r); }}
                onMouseEnter={() => setHoverIdx(i)}
                style={{
                  padding: '9px 12px', cursor: 'pointer', fontSize: 13,
                  borderBottom: '1px solid var(--border-soft)',
                  background: hoverIdx === i ? 'var(--gold-soft)' : 'transparent',
                  display: 'flex', justifyContent: 'space-between', gap: 10,
                }}
              >
                <span className="mono" style={{ color: 'var(--gold)', flexShrink: 0 }}>{r.symbol}</span>
                <span style={{ color: 'var(--text-muted)', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.name || ''}{r.exchange ? ` · ${r.exchange}` : ''}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
