import React, { useEffect } from 'react';
import { NAV_GROUPS, ADMIN_NAV_ITEM } from './navConfig';

export default function NavDrawer({ open, onClose, tab, setTab, isAdmin, username, onLogout }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  const groups = isAdmin
    ? [...NAV_GROUPS, { label: '系統管理', items: [ADMIN_NAV_ITEM] }]
    : NAV_GROUPS;

  const select = (key) => {
    setTab(key);
    onClose();
  };

  return (
    <>
      <div
        className={`drawer-backdrop ${open ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <nav className={`drawer-panel ${open ? 'open' : ''}`}>
        <div className="drawer-header">
          <div className="drawer-mark">
            <svg viewBox="0 0 34 34" fill="none">
              <circle cx="17" cy="17" r="14" stroke="#d4b06a" strokeWidth="1.2" fill="rgba(212,176,106,0.06)" />
              <circle cx="17" cy="17" r="10.2" stroke="#6ee7df" strokeWidth="0.5" opacity="0.45" />
              <polygon points="17,6.5 20.3,17 17,17" fill="#d4b06a" />
              <polygon points="17,6.5 13.7,17 17,17" fill="#e8cd94" opacity="0.85" />
              <polygon points="17,27.5 20.3,17 17,17" fill="#6ee7df" opacity="0.65" />
              <polygon points="17,27.5 13.7,17 17,17" fill="#6ee7df" opacity="0.35" />
              <circle cx="17" cy="17" r="1.7" fill="#08090b" stroke="#d4b06a" strokeWidth="0.8" />
            </svg>
          </div>
          <span className="drawer-title">策略實驗室</span>
          <button className="drawer-close" onClick={onClose} aria-label="關閉選單">✕</button>
        </div>

        <div className="drawer-body">
          {groups.map((group) => (
            <div className="drawer-group" key={group.label}>
              <div className="drawer-group-label">{group.label}</div>
              {group.items.map((item) => (
                <button
                  key={item.key}
                  className={`drawer-item ${tab === item.key ? 'active' : ''}`}
                  onClick={() => select(item.key)}
                >
                  <span className="drawer-item-icon">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="drawer-footer">
          <span className="drawer-username">{username}</span>
          <button className="drawer-logout" onClick={onLogout}>登出</button>
        </div>
      </nav>
    </>
  );
}
