import React, { useState } from 'react';
import { Button, Card, Form, Input, message, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuthStore } from '../../store/auth';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  async function onFinish(values: { email: string; password: string }) {
    setLoading(true);
    try {
      const res = await api.post('/auth/login', values);
      setTokens(res.data.access_token, res.data.refresh_token);
      const meRes = await api.get('/users/me');
      setUser(meRes.data);
      navigate('/dashboard');
    } catch {
      message.error('Invalid email or password');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#0f172a' }}>
      <Card style={{ width: 360 }}>
        <Typography.Title level={3} style={{ marginBottom: 24, textAlign: 'center' }}>
          WZTrack
        </Typography.Title>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input size="large" autoComplete="email" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true }]}>
            <Input.Password size="large" autoComplete="current-password" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              Sign in
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
