import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoginPage from './LoginPage'
import DashboardPage from './DashboardPage'
import SubscriptionDetailPage from './SubscriptionDetailPage'
import AuthGuard from '../components/AuthGuard'

export default function AppRouter() {
  return (
    <Routes>
      {/* Public pages */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected pages — wrapped in AuthGuard */}
      <Route element={<AuthGuard><Layout /></AuthGuard>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/subscription/:id" element={<SubscriptionDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
