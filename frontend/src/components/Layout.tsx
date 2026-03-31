import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import { useT } from '../hooks/useT'
import SettingsMenu from './SettingsMenu'
import { layoutStyles as s } from './Layout.styles'

export default function Layout() {
  const t = useT()
  const navigate = useNavigate()
  const location = useLocation()

  const navLinks = [
    { labelKey: 'dashboard' as const, path: '/dashboard' },
  ]

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

            <Button color="inherit" onClick={() => navigate('/login')} sx={s.loginButton}>
              {t('login')}
            </Button>

            {/* Settings icon */}
            <SettingsMenu />
          </Toolbar>
        </Container>
      </AppBar>

      <Box component="main" className="page-enter" sx={s.main}>
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}
