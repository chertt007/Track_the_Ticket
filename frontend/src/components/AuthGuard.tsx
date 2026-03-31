import { Navigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import { useAppSelector } from '../hooks'
import { authGuardStyles as s } from './AuthGuard.styles'

interface Props {
  children: React.ReactNode
}

// Wraps protected routes. While Amplify resolves the session shows a spinner.
// If not authenticated redirects to /login.
export default function AuthGuard({ children }: Props) {
  const { isAuthenticated, loading } = useAppSelector(st => st.auth)

  if (loading) {
    return (
      <Box sx={s.spinnerBox}>
        <CircularProgress sx={s.spinner} size={40} />
      </Box>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
