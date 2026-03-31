import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { signInWithRedirect } from 'aws-amplify/auth'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Paper from '@mui/material/Paper'
import Divider from '@mui/material/Divider'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import GoogleIcon from '@mui/icons-material/Google'
import { useAppDispatch, useAppSelector } from '../hooks'
import { mockLogin } from '../store/slices/authSlice'
import { useT } from '../hooks/useT'
import { loginStyles as s } from './LoginPage.styles'

export default function LoginPage() {
  const t = useT()
  const dispatch = useAppDispatch()
  const isAuthenticated = useAppSelector(st => st.auth.isAuthenticated)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Already authenticated — redirect straight to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleGoogleSignIn = async () => {
    setError('')
    setLoading(true)
    try {
      await signInWithRedirect({ provider: 'Google' })
      // Page will redirect to Cognito — no need to setLoading(false)
    } catch (err) {
      console.error('signInWithRedirect error:', err)
      setError(t('authError'))
      setLoading(false)
    }
  }

  const handleDevBypass = () => {
    dispatch(mockLogin())
  }

  return (
    <Box sx={s.pageBox}>
      <Paper elevation={0} className="page-enter" sx={s.paper}>
        <Box sx={s.iconCircle}>
          <FlightTakeoffIcon sx={s.icon} />
        </Box>

        <Typography variant="h4" gutterBottom fontWeight={700} color="primary.dark">
          Track the Ticket
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={s.subtitle}>
          {t('authSubtitle')}
        </Typography>

        <Divider sx={s.divider} />

        {error && (
          <Alert severity="error" sx={s.errorAlert}>
            {error}
          </Alert>
        )}

        <Button
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <GoogleIcon />}
          fullWidth
          disabled={loading}
          onClick={handleGoogleSignIn}
          sx={s.googleButton}
        >
          {loading ? t('signingIn') : t('signInWithGoogle')}
        </Button>

        {/* Dev-only bypass — not rendered in production builds */}
        {import.meta.env.DEV && (
          <Button
            variant="text"
            size="small"
            fullWidth
            onClick={handleDevBypass}
            sx={s.devButton}
          >
            {t('devBypass')}
          </Button>
        )}
      </Paper>
    </Box>
  )
}
