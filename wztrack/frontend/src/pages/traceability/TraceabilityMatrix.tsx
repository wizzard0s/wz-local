import React, { useEffect, useState } from 'react';
import { Table, Tag, Tooltip, Typography } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const RUN_COLORS: Record<string, string> = {
  pass: 'green',
  fail: 'red',
  blocked: 'orange',
  skipped: 'default',
};

export default function TraceabilityMatrix() {
  const { projectId } = useParams<{ projectId: string }>();
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    api.get(`/traceability/project/${projectId}`).then((r) => {
      setRows(r.data.data);
      setLoading(false);
    });
  }, [projectId]);

  const columns = [
    {
      title: 'Requirement',
      key: 'req',
      width: 260,
      render: (_: any, row: any) => (
        <div>
          <code style={{ fontSize: 11, color: '#94a3b8' }}>{row.req_id}</code>
          <div style={{ fontSize: 13 }}>{row.title}</div>
          <Tag color={row.status === 'verified' ? 'green' : row.status === 'approved' ? 'blue' : 'default'} style={{ fontSize: 10, marginTop: 2 }}>
            {row.status}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Issues',
      key: 'issues',
      render: (_: any, row: any) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {row.issues.length === 0
            ? <Tooltip title="No linked issues"><Tag icon={<WarningOutlined />} color="orange" className="trace-flag-unplanned">unplanned</Tag></Tooltip>
            : row.issues.map((i: any) => <Tag key={i.id} style={{ fontFamily: 'monospace', fontSize: 11 }}>#{i.sequence_number}</Tag>)
          }
        </div>
      ),
    },
    {
      title: 'Test coverage',
      key: 'tests',
      render: (_: any, row: any) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {row.test_coverage.length === 0
            ? <Tooltip title="No linked test cases"><Tag icon={<WarningOutlined />} color="red" className="trace-flag-untested">untested</Tag></Tooltip>
            : row.test_coverage.map((tc: any, idx: number) => (
              <Tag key={idx} color={tc.latest_run_status ? RUN_COLORS[tc.latest_run_status] : 'default'}>
                {tc.latest_run_status ?? 'no run'}
              </Tag>
            ))
          }
        </div>
      ),
    },
  ];

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 24 }}>Traceability Matrix</Typography.Title>
      <Table columns={columns} dataSource={rows} rowKey="req_id" loading={loading} size="small" pagination={false} />
    </>
  );
}
