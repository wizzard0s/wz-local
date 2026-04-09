import React, { useEffect, useState } from 'react';
import { Button, Card, Input, Layout, List, Typography } from 'antd';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const { Sider, Content } = Layout;

export default function WikiPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [pages, setPages] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');

  async function loadPages() {
    if (!projectId) return;
    const r = await api.get(`/wiki/project/${projectId}?page_size=100`);
    setPages(r.data.data);
  }

  useEffect(() => { loadPages(); }, [projectId]);

  async function saveEdit() {
    if (!selected) return;
    await api.patch(`/wiki/${selected.id}`, { content: draft });
    setEditing(false);
    loadPages();
  }

  return (
    <Layout style={{ background: 'transparent', gap: 16 }}>
      <Sider width={240} style={{ background: 'transparent' }}>
        <Typography.Title level={5} style={{ marginBottom: 12 }}>Wiki</Typography.Title>
        <List
          size="small"
          dataSource={pages}
          renderItem={(p: any) => (
            <List.Item
              onClick={() => { setSelected(p); setDraft(p.content ?? ''); setEditing(false); }}
              style={{ cursor: 'pointer', padding: '6px 12px', background: selected?.id === p.id ? '#1e293b' : 'transparent', borderRadius: 4 }}
            >
              {p.title}
            </List.Item>
          )}
        />
      </Sider>
      <Content>
        {selected ? (
          <Card
            title={selected.title}
            extra={
              editing
                ? <Button type="primary" size="small" onClick={saveEdit}>Save</Button>
                : <Button size="small" onClick={() => setEditing(true)}>Edit</Button>
            }
          >
            {editing ? (
              <Input.TextArea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={20}
                style={{ fontFamily: 'monospace', fontSize: 13 }}
              />
            ) : (
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 14 }}>{selected.content || 'Empty page'}</pre>
            )}
          </Card>
        ) : (
          <Card><Typography.Text type="secondary">Select a page from the list</Typography.Text></Card>
        )}
      </Content>
    </Layout>
  );
}
