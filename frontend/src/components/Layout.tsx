import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { signOut } from 'aws-amplify/auth'
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
import { useT } from '../hooks/useT'
import SettingsMenu from './SettingsMenu'
import { layoutStyles as s } from './Layout.styles'

export default function Layout() {
  const t = useT()
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useAppDispatch()
  const user = useAppSelector(st => st.auth.user)

  const navLinks = [
    { labelKey: 'dashboard' as const, path: '/dashboard' },
  ]

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch {
      // If Cognito sign-out fails (e.g. dev mode), clear Redux state manually
    } finally {
      dispatch(clearAuth())
      navigate('/login')
    }
  }

  // User avatar initials derived from email
  const avatarLetter = user?.email?.[0]?.toUpperCase() ?? '?'

  return (
    <Box sx={s.root}>
      <AppBar position="sticky" elevation={0}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={s.toolbar}>
            {/* Logo */}
            <Box sx={s.logoBox} onClick={() => navigate('/dashboard')}>
              <FlightTakeoffIcon sx={s.logoIcon} />
              <Typography variant="h6" sx={s.logoText}>
                {t('appName')}
              </Typography>
            </Box>

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
              <Tooltip title={user.email}>
                <Avatar src={user.picture} sx={s.avatar}>
                  {!user.picture && avatarLetter}
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
    </Box>
  )
}
