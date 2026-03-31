import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()

  const navLinks = [
    { label: 'Dashboard', path: '/dashboard' },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* ── AppBar ──────────────────────────────────────────────────────── */}
      <AppBar position="sticky" elevation={0}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ py: { xs: 0.5, sm: 1 } }}>
            {/* Логотип */}
            <Box
              sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer', flexGrow: 1 }}
              onClick={() => navigate('/dashboard')}
            >
              <FlightTakeoffIcon sx={{ fontSize: { xs: 22, sm: 26 } }} />
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: '1rem', sm: '1.2rem' },
                  letterSpacing: '-0.01em',
                }}
              >
                Track the Ticket
              </Typography>
            </Box>

            {/* Навигация */}
            {navLinks.map(link => (
              <Button
                key={link.path}
                color="inherit"
                onClick={() => navigate(link.path)}
                sx={{
                  fontWeight: location.pathname === link.path ? 700 : 400,
                  opacity: location.pathname === link.path ? 1 : 0.8,
                  borderBottom: location.pathname === link.path
                    ? '2px solid rgba(255,255,255,0.8)'
                    : '2px solid transparent',
                  borderRadius: 0,
                  px: 1.5,
                  fontSize: { xs: '0.85rem', sm: '0.95rem' },
                }}
              >
                {link.label}
              </Button>
            ))}

            <Button
              color="inherit"
              onClick={() => navigate('/login')}
              sx={{ ml: 1, opacity: 0.85, fontSize: { xs: '0.85rem', sm: '0.95rem' } }}
            >
              Login
            </Button>
          </Toolbar>
        </Container>
      </AppBar>

      {/* ── Контент ────────────────────────────────────────────────────── */}
      <Box
        component="main"
        className="page-enter"
        sx={{
          flexGrow: 1,
          py: { xs: 3, sm: 4, md: 5 },
          px: { xs: 2, sm: 3 },
        }}
      >
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}
