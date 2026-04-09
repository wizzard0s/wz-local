import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography } from 'antd';
import { CheckCircleOutlined, FundOutlined, ProjectOutlined, BugOutlined } from '@ant-design/icons';
import api from '../../services/api';

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    api.get('/projects').then((r) => setProjects(r.data.data));
  }, []);

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 24 }}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Projects" value={projects.length} prefix={<ProjectOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Open Issues" value="—" prefix={<BugOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Test Pass Rate" value="—" suffix="%" prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Requirements" value="—" prefix={<FundOutlined />} />
          </Card>
        </Col>
      </Row>

      <Typography.Title level={5} style={{ marginTop: 32, marginBottom: 16 }}>Your Projects</Typography.Title>
      <Row gutter={[16, 16]}>
        {projects.map((p: any) => (
          <Col xs={24} sm={12} lg={8} key={p.id}>
            <Card
              hoverable
              title={<><span style={{ fontFamily: 'monospace', marginRight: 8, color: '#6366f1' }}>{p.key}</span>{p.name}</>}
            >
              <Typography.Text type="secondary">{p.description || 'No description'}</Typography.Text>
            </Card>
          </Col>
        ))}
      </Row>
    </>
  );
}
