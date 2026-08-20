// 全站導覽用的分頁清單，NavDrawer（側邊選單）跟 App（頁面標題列）共用同一份，
// 避免兩處各寫一份重複資料、之後改動漏掉其中一邊
export const NAV_GROUPS = [
  {
    label: '總覽',
    items: [{ key: 'home', label: '首頁', icon: '🏠' }],
  },
  {
    label: '回測分析',
    items: [
      { key: 'backtest', label: '回測', icon: '📊' },
      { key: 'compare', label: '策略比較', icon: '🆚' },
      { key: 'optimize', label: '參數最佳化', icon: '🎯' },
    ],
  },
  {
    label: '盤勢監控',
    items: [
      { key: 'stockcheck', label: '個股分析', icon: '🔍' },
      { key: 'futures', label: '美股期貨', icon: '⚔️' },
      { key: 'watchlist', label: '追蹤清單', icon: '🔔' },
    ],
  },
];

export const ADMIN_NAV_ITEM = { key: 'admin', label: '管理員', icon: '👤' };

// key -> {label, icon} 的扁平對照表，方便直接查單一分頁的顯示名稱
export const NAV_ITEM_BY_KEY = Object.fromEntries(
  [...NAV_GROUPS.flatMap((g) => g.items), ADMIN_NAV_ITEM].map((item) => [item.key, item])
);
