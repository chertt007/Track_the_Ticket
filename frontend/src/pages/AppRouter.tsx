import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoginPage from './LoginPage'
import DashboardPage from './DashboardPage'
import SubscriptionDetailPage from './SubscriptionDetailPage'

export default function AppRouter() {
  return (
    <Routes>
      {/* Pages without Layout */}
      <Route path="/login" element={<LoginPage />} />

      {/* Pages with Layout (AppBar + navigation) */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/subscription/:id" element={<SubscriptionDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
