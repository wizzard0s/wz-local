import React, { useEffect, useState } from 'react';
import { Button, Card, Col, Row, Table, Tag, Typography, message } from 'antd';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

export default function TestPlanList() {
  const { projectId } = useParams<{ projectId: string }>();
  const [plans, setPlans] = useState<any[]>([]);

  useEffect(() => {
    if (!projectId) return;
    api.get(`/testcases/plans/project/${projectId}?page_size=100`).then((r) => setPlans(r.data.data));
  }, [projectId]);

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={v === 'completed' ? 'green' : v === 'active' ? 'blue' : 'default'}>{v}</Tag>,
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 180, render: (v: string) => new Date(v).toLocaleDateString('en-ZA') },
  ];

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 24 }}>Test Plans</Typography.Title>
      <Table columns={columns} dataSource={plans} rowKey="id" size="small" />
    </>
  );
}
