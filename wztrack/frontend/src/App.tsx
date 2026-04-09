import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useAuthStore } from './store/auth';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/auth/Login';
import Dashboard from './pages/dashboard/Dashboard';
import ProjectList from './pages/projects/ProjectList';
import KanbanBoard from './pages/kanban/KanbanBoard';
import RequirementList from './pages/requirements/RequirementList';
import WikiPage from './pages/wiki/WikiPage';
import TestPlanList from './pages/testcases/TestPlanList';
import TraceabilityMatrix from './pages/traceability/TraceabilityMatrix';
import UserManagement from './pages/settings/UserManagement';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/projects" element={<ProjectList />} />
                  <Route path="/projects/:projectId/board" element={<KanbanBoard />} />
                  <Route path="/projects/:projectId/requirements" element={<RequirementList />} />
                  <Route path="/projects/:projectId/wiki" element={<WikiPage />} />
                  <Route path="/projects/:projectId/tests" element={<TestPlanList />} />
                  <Route path="/projects/:projectId/traceability" element={<TraceabilityMatrix />} />
                  <Route path="/settings/users" element={<UserManagement />} />
                </Routes>
              </AppLayout>
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
