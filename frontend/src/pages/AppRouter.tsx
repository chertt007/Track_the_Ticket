import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoginPage from './LoginPage'
import DashboardPage from './DashboardPage'
import SubscriptionDetailPage from './SubscriptionDetailPage'

export default function AppRouter() {
  return (
    <Routes>
      {/* Страницы без Layout */}
      <Route path="/login" element={<LoginPage />} />

      {/* Страницы с Layout (AppBar + навигация) */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/subscription/:id" element={<SubscriptionDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
