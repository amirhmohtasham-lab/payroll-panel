// Route definitions — every page is guarded by ProtectedRoute (role-based).

import { Navigate, Route, BrowserRouter, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { OperatorPage } from './pages/OperatorPage';
import { DashboardPage } from './pages/DashboardPage';
import { ArchivePage } from './pages/ArchivePage';
import { ReportsPage } from './pages/ReportsPage';
import { ChatPage } from './pages/ChatPage';
import { FertilizerPage } from './pages/FertilizerPage';
import { UsersPage } from './pages/UsersPage';
import { GreenhousePage } from './pages/GreenhousePage';
import { SoilGreenhousePage } from './pages/SoilGreenhousePage';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/operator"
            element={
              <ProtectedRoute allowedRoles={['operator']}>
                <OperatorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/archive"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <ArchivePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/fertilizer"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <FertilizerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/greenhouse"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <GreenhousePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/greenhouse/soil"
            element={
              <ProtectedRoute allowedRoles={['accountant']}>
                <SoilGreenhousePage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
