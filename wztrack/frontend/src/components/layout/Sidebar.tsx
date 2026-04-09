import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import {
  AppstoreOutlined,
  BugOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  FileTextOutlined,
  LogoutOutlined,
  UserOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/auth';

const { Sider } = Layout;

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);

  const items = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/projects', icon: <AppstoreOutlined />, label: 'Projects' },
    { type: 'divider' as const },
    { key: '/settings/users', icon: <UserOutlined />, label: 'Users' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign out',
      danger: true,
      onClick: () => { logout(); navigate('/login'); },
    },
  ];

  return (
    <Sider
      width={220}
      style={{ position: 'fixed', left: 0, top: 0, height: '100vh', overflow: 'auto', zIndex: 100 }}
    >
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155' }}>
        <Typography.Text strong style={{ fontSize: 18, color: '#e2e8f0', letterSpacing: '-0.5px' }}>
          WZTrack
        </Typography.Text>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={items}
        onClick={({ key }) => { if (key !== 'logout') navigate(key); }}
        style={{ borderRight: 0, marginTop: 8 }}
      />
    </Sider>
  );
}
