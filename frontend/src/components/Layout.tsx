import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { signOut } from 'firebase/auth'
import { auth } from '../config/firebase'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Tooltip from '@mui/material/Tooltip'
import Avatar from '@mui/material/Avatar'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import LogoutIcon from '@mui/icons-material/Logout'
import { useAppDispatch, useAppSelector } from '../hooks'
import { clearAuth } from '../store/slices/authSlice'
import { setLanguage } from '../store/slices/settingsSlice'
import { useT } from '../hooks/useT'
import SettingsMenu from './SettingsMenu'
import InstallPromptBanner from './InstallPromptBanner'
import HeaderSkyWidget from './HeaderSkyWidget'
import { layoutStyles as s } from './Layout.styles'

export default function Layout() {
  const t = useT()
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useAppDispatch()
  const user = useAppSelector(st => st.auth.user)
  const language = useAppSelector(st => st.settings.language)

  const navLinks = [
    { labelKey: 'dashboard' as const, path: '/dashboard' },
  ]

  const handleSignOut = async () => {
    try {
      await signOut(auth)
    } catch {
      // Surface nothing — onAuthStateChanged still fires and clears state
    } finally {
      dispatch(clearAuth())
      navigate('/login')
    }
  }

  // Avatar initial from displayName, falling back to email, then '?'
  const avatarLetter =
    user?.displayName?.[0]?.toUpperCase() ??
    user?.email?.[0]?.toUpperCase() ??
    '?'

  return (
    <Box sx={s.root}>
      <AppBar position="sticky" elevation={0}>
        {/* Floating clouds drifting across the header */}
        <Box sx={s.cloudLayer}>
          <Box sx={s.cloud(135, 38, '18%', 38, 0)} />
          <Box sx={s.cloud(88, 27, '58%', 27, -13)} />
          <Box sx={s.cloud(58, 18, '28%', 19, -7)} />
        </Box>

        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Toolbar disableGutters sx={s.toolbar}>
            {/* Logo */}
            <Box sx={s.logoBox} onClick={() => navigate('/dashboard')}>
              <FlightTakeoffIcon sx={s.logoIcon} />
              <Typography variant="h6" sx={s.logoText}>
                {t('appName')}
              </Typography>
            </Box>

            {/* Sun / cloud / plane weather widget */}
            <HeaderSkyWidget />

            {/* Nav links */}
            {navLinks.map(link => (
              <Button
                key={link.path}
                color="inherit"
                onClick={() => navigate(link.path)}
                sx={s.navButton(location.pathname === link.path)}
              >
                {t(link.labelKey)}
              </Button>
            ))}

            {/* User avatar — shows Google profile photo when available */}
            {user && (
              <Tooltip title={user.email ?? ''}>
                <Avatar src={user.photoURL ?? undefined} sx={s.avatar}>
                  {!user.photoURL && avatarLetter}
                </Avatar>
              </Tooltip>
            )}

            {/* Sign out */}
            <Tooltip title={t('signOut')}>
              <Button
                color="inherit"
                onClick={handleSignOut}
                startIcon={<LogoutIcon sx={{ fontSize: 18 }} />}
                sx={s.signOutButton}
              >
                {t('signOut')}
              </Button>
            </Tooltip>

            {/* Language quick-toggle */}
            <Tooltip title={language === 'en' ? 'Switch to Russian' : 'Переключить на English'}>
              <Button
                color="inherit"
                onClick={() => dispatch(setLanguage(language === 'en' ? 'ru' : 'en'))}
                sx={s.langToggle}
              >
                {language === 'en' ? 'EN' : 'RU'}
              </Button>
            </Tooltip>

            {/* Settings icon */}
            <SettingsMenu />
          </Toolbar>
        </Container>
      </AppBar>

      <Box component="main" sx={s.main}>
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>

      {/* PWA install prompt — appears automatically in supported browsers */}
      <InstallPromptBanner />
    </Box>
  )
}
