import React, { useEffect, useState } from 'react';
import { Button, Form, Input, Modal, Table, Tag, Typography, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  approved: 'blue',
  implemented: 'gold',
  verified: 'green',
};

export default function RequirementList() {
  const { projectId } = useParams<{ projectId: string }>();
  const [requirements, setRequirements] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function load() {
    if (!projectId) return;
    const r = await api.get(`/requirements/project/${projectId}?page_size=100`);
    setRequirements(r.data.data);
  }

  useEffect(() => { load(); }, [projectId]);

  async function onCreate(values: any) {
    try {
      await api.post(`/requirements/project/${projectId}`, values);
      message.success('Requirement created');
      setOpen(false);
      form.resetFields();
      load();
    } catch (e: any) {
      message.error(e.response?.data?.detail ?? 'Failed');
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'req_id', key: 'req_id', width: 140, render: (v: string) => <code style={{ fontSize: 12 }}>{v}</code> },
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 100 },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={STATUS_COLORS[v] ?? 'default'}>{v}</Tag>,
    },
    { title: 'Version', dataIndex: 'current_version', key: 'current_version', width: 80 },
  ];

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>Requirements</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>New requirement</Button>
      </div>

      <Table columns={columns} dataSource={requirements} rowKey="id" size="small" />

      <Modal title="New requirement" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} okText="Create">
        <Form form={form} layout="vertical" onFinish={onCreate} style={{ marginTop: 16 }}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="acceptance_criteria" label="Acceptance criteria">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="priority" label="Priority" initialValue="must">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
