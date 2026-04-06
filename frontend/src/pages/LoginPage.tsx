import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  signIn,
  signUp,
  confirmSignUp,
  resetPassword,
  confirmResetPassword,
  resendSignUpCode,
  signInWithRedirect,
} from 'aws-amplify/auth'
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
import { useAppDispatch, useAppSelector } from '../hooks'
import { mockLogin } from '../store/slices/authSlice'
import { useT } from '../hooks/useT'
import { loginStyles as s } from './LoginPage.styles'

// Five auth screens inside one page — no separate routes needed
type AuthView = 'login' | 'signup' | 'confirmSignup' | 'forgotPassword' | 'newPassword'

export default function LoginPage() {
  const t = useT()
  const dispatch = useAppDispatch()
  const isAuthenticated = useAppSelector(st => st.auth.isAuthenticated)

  const [view, setView] = useState<AuthView>('login')

  // Shared form state — fields are reused across views where sensible
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [code, setCode] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmNewPw, setConfirmNewPw] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  // Already authenticated — go straight to dashboard
  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  const clearMessages = () => { setError(''); setInfo('') }
  const switchView = (v: AuthView) => { clearMessages(); setCode(''); setView(v) }

  // ── Sign in with Google ──────────────────────────────────────────────────

  const handleGoogleSignIn = async () => {
    clearMessages()
    setLoading(true)
    try {
      await signInWithRedirect({ provider: 'Google' })
      // Page redirects to Cognito — loading stays true
    } catch {
      setError(t('authError'))
      setLoading(false)
    }
  }

  // ── Sign in with email / password ────────────────────────────────────────

  const handleEmailSignIn = async () => {
    clearMessages()
    if (!email) { setError(t('emailRequired')); return }
    if (!password) { setError(t('passwordRequired')); return }
    setLoading(true)
    try {
      const { nextStep } = await signIn({ username: email, password })
      if (nextStep.signInStep === 'CONFIRM_SIGN_UP') {
        // Registered but never confirmed — send to confirmation view
        setLoading(false)
        switchView('confirmSignup')
        return
      }
      // DONE: Hub fires 'signedIn' → useAuth resolves session → isAuthenticated becomes true
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
      setLoading(false)
    }
  }

  // ── Register ─────────────────────────────────────────────────────────────

  const handleSignUp = async () => {
    clearMessages()
    if (!email) { setError(t('emailRequired')); return }
    if (!password) { setError(t('passwordRequired')); return }
    if (password !== confirmPassword) { setError(t('passwordMismatch')); return }
    setLoading(true)
    try {
      await signUp({ username: email, password, options: { userAttributes: { email } } })
      switchView('confirmSignup')
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
    } finally {
      setLoading(false)
    }
  }

  // ── Confirm email after registration ─────────────────────────────────────

  const handleConfirmSignUp = async () => {
    clearMessages()
    if (!code) { setError(t('codeRequired')); return }
    setLoading(true)
    try {
      await confirmSignUp({ username: email, confirmationCode: code })
      // Auto sign-in after confirmation
      const { nextStep } = await signIn({ username: email, password })
      if (nextStep.signInStep !== 'DONE') {
        // Unexpected extra step — just send back to login
        switchView('login')
        setInfo(t('confirmSuccessSignIn'))
      }
      // DONE: Hub fires 'signedIn' → session resolves automatically
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
      setLoading(false)
    }
  }

  const handleResendCode = async () => {
    clearMessages()
    try {
      await resendSignUpCode({ username: email })
      setInfo(t('codeSentAgain'))
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
    }
  }

  // ── Request password reset ────────────────────────────────────────────────

  const handleForgotPassword = async () => {
    clearMessages()
    if (!email) { setError(t('emailRequired')); return }
    setLoading(true)
    try {
      await resetPassword({ username: email })
      switchView('newPassword')
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
    } finally {
      setLoading(false)
    }
  }

  // ── Submit new password ───────────────────────────────────────────────────

  const handleResetPassword = async () => {
    clearMessages()
    if (!code) { setError(t('codeRequired')); return }
    if (!newPw) { setError(t('passwordRequired')); return }
    if (newPw !== confirmNewPw) { setError(t('passwordMismatch')); return }
    setLoading(true)
    try {
      await confirmResetPassword({ username: email, confirmationCode: code, newPassword: newPw })
      switchView('login')
      setInfo(t('passwordResetDone'))
    } catch (err: any) {
      setError(err?.message ?? t('authError'))
    } finally {
      setLoading(false)
    }
  }

  // ── View titles map ───────────────────────────────────────────────────────

  const titles: Partial<Record<AuthView, string>> = {
    signup: t('signUpTitle'),
    confirmSignup: t('confirmSignUpTitle'),
    forgotPassword: t('forgotPasswordTitle'),
    newPassword: t('newPasswordTitle'),
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <Box sx={s.pageBox}>
      <Paper elevation={0} className="page-enter" sx={s.paper}>

        {/* Header */}
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

        {/* Alerts */}
        {error && <Alert severity="error" sx={s.errorAlert}>{error}</Alert>}
        {info && <Alert severity="success" sx={s.infoAlert}>{info}</Alert>}

        {/* ── LOGIN ─────────────────────────────────────────────────────── */}
        {view === 'login' && (
          <>
            {/* Google button */}
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

            {/* OR divider */}
            <Divider sx={s.orDivider}>
              <Typography component="span" sx={s.orText}>{t('orDivider')}</Typography>
            </Divider>

            {/* Email / password */}
            <Box sx={s.formBox}>
              <TextField
                label={t('emailLabel')}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                fullWidth
                size="small"
                sx={s.textField}
                disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleEmailSignIn()}
              />
              <TextField
                label={t('passwordLabel')}
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                fullWidth
                size="small"
                sx={s.textField}
                disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleEmailSignIn()}
              />
              <Button
                variant="outlined"
                fullWidth
                size="large"
                disabled={loading}
                onClick={handleEmailSignIn}
                sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('signInButton')}
              </Button>
            </Box>

            {/* Secondary links */}
            <Box sx={s.linksRow}>
              <Button size="small" sx={s.linkButton} onClick={() => switchView('forgotPassword')}>
                {t('forgotPasswordLink')}
              </Button>
              <Button size="small" sx={s.linkButton} onClick={() => switchView('signup')}>
                {t('registerLink')}
              </Button>
            </Box>

            {import.meta.env.DEV && (
              <Button
                variant="text"
                size="small"
                fullWidth
                onClick={() => dispatch(mockLogin())}
                sx={s.devButton}
              >
                {t('devBypass')}
              </Button>
            )}
          </>
        )}

        {/* ── SIGN UP ───────────────────────────────────────────────────── */}
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

        {/* ── CONFIRM SIGNUP ────────────────────────────────────────────── */}
        {view === 'confirmSignup' && (
          <>
            <Typography variant="body2" color="text.secondary" sx={s.viewHint}>
              {t('confirmSignUpHint')} <strong>{email}</strong>
            </Typography>
            <Box sx={s.formBox}>
              <TextField
                label={t('codeLabel')}
                value={code}
                onChange={e => setCode(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                inputProps={{ maxLength: 6, inputMode: 'numeric' }}
                onKeyDown={e => e.key === 'Enter' && handleConfirmSignUp()}
              />
              <Button
                variant="contained" fullWidth size="large"
                disabled={loading} onClick={handleConfirmSignUp} sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('confirmEmailButton')}
              </Button>
            </Box>
            <Box sx={s.linksRow}>
              <Button size="small" sx={s.linkButton} onClick={handleResendCode}>
                {t('resendCodeLink')}
              </Button>
              <Button size="small" sx={s.linkButton} onClick={() => switchView('login')}>
                {t('backLink')}
              </Button>
            </Box>
          </>
        )}

        {/* ── FORGOT PASSWORD ───────────────────────────────────────────── */}
        {view === 'forgotPassword' && (
          <>
            <Typography variant="body2" color="text.secondary" sx={s.viewHint}>
              {t('forgotPasswordHint')}
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
                {loading ? t('signingIn') : t('sendCodeButton')}
              </Button>
            </Box>
            <Button size="small" sx={s.linkButton} onClick={() => switchView('login')}>
              {t('backLink')}
            </Button>
          </>
        )}

        {/* ── NEW PASSWORD ──────────────────────────────────────────────── */}
        {view === 'newPassword' && (
          <>
            <Typography variant="body2" color="text.secondary" sx={s.viewHint}>
              {t('confirmSignUpHint')} <strong>{email}</strong>
            </Typography>
            <Box sx={s.formBox}>
              <TextField
                label={t('codeLabel')}
                value={code}
                onChange={e => setCode(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                inputProps={{ maxLength: 6, inputMode: 'numeric' }}
              />
              <TextField
                label={t('newPasswordLabel')}
                type="password"
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
              />
              <TextField
                label={t('confirmPasswordLabel')}
                type="password"
                value={confirmNewPw}
                onChange={e => setConfirmNewPw(e.target.value)}
                fullWidth size="small" sx={s.textField} disabled={loading}
                onKeyDown={e => e.key === 'Enter' && handleResetPassword()}
              />
              <Button
                variant="contained" fullWidth size="large"
                disabled={loading} onClick={handleResetPassword} sx={s.submitButton}
              >
                {loading ? t('signingIn') : t('savePasswordButton')}
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
