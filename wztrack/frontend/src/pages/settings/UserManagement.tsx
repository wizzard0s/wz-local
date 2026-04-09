import React, { useEffect, useState } from 'react';
import { Button, Form, Input, Modal, Select, Table, Tag, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '../../services/api';

const ROLES = ['admin', 'manager', 'developer', 'qa', 'viewer'];
const ROLE_COLORS: Record<string, string> = {
  admin: 'red', manager: 'blue', developer: 'cyan', qa: 'gold', viewer: 'default',
};

export default function UserManagement() {
  const [users, setUsers] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function load() {
    const r = await api.get('/users');
    setUsers(r.data.data);
  }

  useEffect(() => { load(); }, []);

  async function onCreate(values: any) {
    try {
      await api.post('/users', values);
      message.success('User created');
      setOpen(false);
      form.resetFields();
      load();
    } catch (e: any) {
      message.error(e.response?.data?.detail ?? 'Failed');
    }
  }

  const columns = [
    { title: 'Name', dataIndex: 'display_name', key: 'display_name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Role', dataIndex: 'role', key: 'role', render: (v: string) => <Tag color={ROLE_COLORS[v] ?? 'default'}>{v}</Tag> },
    { title: 'Active', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Active' : 'Disabled'}</Tag> },
  ];

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>User Management</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>New user</Button>
      </div>

      <Table columns={columns} dataSource={users} rowKey="id" size="small" />

      <Modal title="New user" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Create">
        <Form form={form} layout="vertical" onFinish={onCreate} style={{ marginTop: 16 }}>
          <Form.Item name="display_name" label="Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="Role" initialValue="viewer">
            <Select options={ROLES.map((r) => ({ value: r, label: r }))} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
