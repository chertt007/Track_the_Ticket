import { Navigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import { useAppSelector } from '../hooks'
import { authGuardStyles as s } from './AuthGuard.styles'

interface Props {
  children: React.ReactNode
}

export default function AuthGuard({ children }: Props) {
  const user = useAppSelector(st => st.auth.user)
  const loading = useAppSelector(st => st.auth.loading)

  if (loading) {
    return (
      <Box sx={s.spinnerBox}>
        <CircularProgress sx={s.spinner} />
      </Box>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
