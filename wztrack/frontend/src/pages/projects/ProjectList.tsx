import React, { useEffect, useState } from 'react';
import { Button, Card, Col, Form, Input, Modal, Row, Tag, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

export default function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  async function load() {
    const r = await api.get('/projects');
    setProjects(r.data.data);
  }

  useEffect(() => { load(); }, []);

  async function onCreate(values: any) {
    try {
      await api.post('/projects', values);
      message.success('Project created');
      setOpen(false);
      form.resetFields();
      load();
    } catch (e: any) {
      message.error(e.response?.data?.detail ?? 'Failed to create project');
    }
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Projects</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>New project</Button>
      </div>

      <Row gutter={[16, 16]}>
        {projects.map((p: any) => (
          <Col xs={24} sm={12} lg={8} key={p.id}>
            <Card
              hoverable
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Tag color="blue" style={{ fontFamily: 'monospace' }}>{p.key}</Tag>
                  {p.name}
                </div>
              }
              extra={<Tag color={p.status === 'active' ? 'green' : 'default'}>{p.status}</Tag>}
              onClick={() => navigate(`/projects/${p.id}/board`)}
            >
              <Typography.Text type="secondary">{p.description || 'No description'}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>

      <Modal title="New project" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Create">
        <Form form={form} layout="vertical" onFinish={onCreate} style={{ marginTop: 16 }}>
          <Form.Item name="key" label="Project key" rules={[{ required: true }, { pattern: /^[A-Z]{2,10}$/, message: 'Use 2-10 uppercase letters (e.g. CHAT)' }]}>
            <Input placeholder="CHAT" style={{ textTransform: 'uppercase' }} />
          </Form.Item>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="WizzardChat" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
