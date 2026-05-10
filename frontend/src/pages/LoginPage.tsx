import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signInWithPopup,
  signInWithRedirect,
} from 'firebase/auth'
import { FirebaseError } from 'firebase/app'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Paper from '@mui/material/Paper'
import Divider from '@mui/material/Divider'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import TextField from '@mui/material/TextField'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import GoogleIcon from '@mui/icons-material/Google'
import { auth, googleProvider } from '../config/firebase'
import { useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import { loginStyles as s } from './LoginPage.styles'

type AuthView = 'login' | 'signup' | 'forgotPassword'

// Use redirect on touch devices — popup UX is broken in mobile browsers.
const isMobile = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(max-width: 768px)').matches

export default function LoginPage() {
  const t = useT()
  const user = useAppSelector(st => st.auth.user)

  const [view, setView] = useState<AuthView>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  if (user) return <Navigate to="/dashboard" replace />

  const clearMessages = () => { setError(''); setInfo('') }
  const switchView = (v: AuthView) => { clearMessages(); setView(v) }

  // Map Firebase error codes to localized strings — fall back to a generic message.
  const friendlyError = (err: unknown): string => {
    if (err instanceof FirebaseError) {
      switch (err.code) {
        case 'auth/invalid-email':         return t('errInvalidEmail')
        case 'auth/user-not-found':
        case 'auth/wrong-password':
        case 'auth/invalid-credential':    return t('errWrongCredentials')
        case 'auth/email-already-in-use':  return t('errEmailInUse')
        case 'auth/weak-password':         return t('errWeakPassword')
        case 'auth/popup-closed-by-user':  return t('errPopupClosed')
        case 'auth/network-request-failed': return t('errNetwork')
        default:                           return `${t('authError')} [${err.code}]`
      }
    }
    return `${t('authError')} [${(err as Error)?.message ?? 'unknown'}]`
  }

  const handleGoogleSignIn = async () => {
    clearMessages()
    setLoading(true)
    try {
      if (isMobile()) {
        await signInWithRedirect(auth, googleProvider)
        // Page navigates away — loading stays true until redirect completes
      } else {
        await signInWithPopup(auth, googleProvider)
        // onAuthStateChanged fires → AuthGuard lets us through
      }
    } catch (err) {
      console.error('[google-signin]', err)
      setError(friendlyError(err))
      setLoading(false)
    }
  }

  const handleEmailSignIn = async () => {
    clearMessages()
    if (!email)    { setError(t('emailRequired')); return }
    if (!password) { setError(t('passwordRequired')); return }
    setLoading(true)
    try {
      await signInWithEmailAndPassword(auth, email, password)
    } catch (err) {
      setError(friendlyError(err))
      setLoading(false)
    }
  }

  const handleSignUp = async () => {
    clearMessages()
    if (!email)    { setError(t('emailRequired')); return }
    if (!password) { setError(t('passwordRequired')); return }
    if (password !== confirmPassword) { setError(t('passwordMismatch')); return }
    setLoading(true)
    try {
      await createUserWithEmailAndPassword(auth, email, password)
    } catch (err) {
      setError(friendlyError(err))
      setLoading(false)
    }
  }

  const handleForgotPassword = async () => {
    clearMessages()
    if (!email) { setError(t('emailRequired')); return }
    setLoading(true)
    try {
      await sendPasswordResetEmail(auth, email)
      setInfo(t('passwordResetEmailSent'))
      switchView('login')
    } catch (err) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  const titles: Partial<Record<AuthView, string>> = {
    signup:         t('signUpTitle'),
    forgotPassword: t('forgotPasswordTitle'),
  }

  return (
    <Box sx={s.pageBox}>
      <Paper elevation={0} className="page-enter" sx={s.paper}>
        <Box sx={s.iconCircle}>
          <FlightTakeoffIcon sx={s.icon} />
        </Box>
        <Typography variant="h4" gutterBottom fontWeight={700} color="primary.dark">
          {view === 'login' ? 'Track the Ticket' : titles[view]}
        </Typography>
        {view === 'login' && (
          <Typography variant="body1" color="text.secondary" sx={s.subtitle}>
            {t('authSubtitle')}
          </Typography>
        )}

        <Divider sx={s.divider} />

        {error && <Alert severity="error" sx={s.errorAlert}>{error}</Alert>}
        {info  && <Alert severity="success" sx={s.infoAlert}>{info}</Alert>}

        {view === 'login' && (
          <>
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

            <Divider sx={s.orDivider}>
              <Typography component="span" sx={s.orText}>{t('orDivider')}</Typography>
            </Divider>

            <Box sx={s.formBox}>
              <TextField
                label={t('emailLabel')}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleEmailSignIn()}
              />
              <TextField
                label={t('passwordLabel')}
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleEmailSignIn()}
              />
              <Button
                variant="outlined" fullWidth size="large"
                disabled={loading} onClick={handleEmailSignIn} sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('signInButton')}
              </Button>
            </Box>

            <Box sx={s.linksRow}>
              <Button size="small" sx={s.linkButton} onClick={() => switchView('forgotPassword')}>
                {t('forgotPasswordLink')}
              </Button>
              <Button size="small" sx={s.linkButton} onClick={() => switchView('signup')}>
                {t('registerLink')}
              </Button>
            </Box>
          </>
        )}

        {view === 'signup' && (
          <>
            <Box sx={s.formBox}>
              <TextField
                label={t('emailLabel')}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
              />
              <TextField
                label={t('passwordLabel')}
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
              />
              <TextField
                label={t('confirmPasswordLabel')}
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleSignUp()}
              />
              <Button
                variant="contained" fullWidth size="large"
                disabled={loading} onClick={handleSignUp} sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('registerButton')}
              </Button>
            </Box>
            <Button size="small" sx={s.linkButton} onClick={() => switchView('login')}>
              {t('alreadyHaveAccountLink')}
            </Button>
          </>
        )}

        {view === 'forgotPassword' && (
          <>
            <Typography variant="body2" color="text.secondary" sx={s.viewHint}>
              {t('forgotPasswordHintFirebase')}
            </Typography>
            <Box sx={s.formBox}>
              <TextField
                label={t('emailLabel')}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleForgotPassword()}
              />
              <Button
                variant="contained" fullWidth size="large"
                disabled={loading} onClick={handleForgotPassword} sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('sendResetLinkButton')}
              </Button>
            </Box>
            <Button size="small" sx={s.linkButton} onClick={() => switchView('login')}>
              {t('backLink')}
            </Button>
          </>
        )}
      </Paper>
    </Box>
  )
}
