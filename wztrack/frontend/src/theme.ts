import type { ThemeConfig } from 'antd';

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#6366f1',
    colorBgBase: '#0f172a',
    colorBgContainer: '#1e293b',
    colorBgElevated: '#1e293b',
    colorBorder: '#334155',
    colorText: '#e2e8f0',
    colorTextSecondary: '#94a3b8',
    colorTextPlaceholder: '#64748b',
    borderRadius: 6,
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  components: {
    Layout: {
      siderBg: '#0f172a',
      headerBg: '#1e293b',
      bodyBg: '#0f172a',
    },
    Menu: {
      darkItemBg: '#0f172a',
      darkItemSelectedBg: '#334155',
      darkItemHoverBg: '#1e293b',
    },
    Table: {
      headerBg: '#1e293b',
    },
  },
};
