import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Tag, Typography } from 'antd';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const CATEGORY_COLORS: Record<string, string> = {
  backlog: '#6b7280',
  in_progress: '#3b82f6',
  review: '#f59e0b',
  done: '#10b981',
  cancelled: '#ef4444',
};

export default function KanbanBoard() {
  const { projectId } = useParams<{ projectId: string }>();
  const [states, setStates] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([
      api.get(`/projects/${projectId}/states`),
      api.get(`/issues/project/${projectId}?page_size=100`),
    ]).then(([statesRes, issuesRes]) => {
      setStates(statesRes.data);
      setIssues(issuesRes.data.data);
    });
  }, [projectId]);

  const byState = (stateId: string) => issues.filter((i) => i.status_id === stateId);

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 24 }}>Board</Typography.Title>
      <div className="kanban-board">
        {states.map((state) => (
          <div key={state.id} className="kanban-column">
            <div
              className="kanban-column-header"
              style={{ background: CATEGORY_COLORS[state.category] ?? '#334155', color: '#fff' }}
            >
              {state.name}
              <Tag style={{ marginLeft: 8, fontSize: 11 }}>{byState(state.id).length}</Tag>
            </div>
            {byState(state.id).map((issue) => (
              <Card key={issue.id} size="small" className="kanban-card" bordered={false}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 11, fontFamily: 'monospace' }}>
                    #{issue.sequence_number}
                  </Typography.Text>
                  <Tag style={{ fontSize: 10, lineHeight: '16px' }}>{issue.type}</Tag>
                </div>
                <Typography.Text style={{ fontSize: 13 }}>{issue.title}</Typography.Text>
              </Card>
            ))}
          </div>
        ))}
      </div>
    </>
  );
}
