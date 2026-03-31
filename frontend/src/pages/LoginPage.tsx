import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Paper from '@mui/material/Paper'
import Divider from '@mui/material/Divider'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import GoogleIcon from '@mui/icons-material/Google'
import { alpha } from '@mui/material/styles'
import { berryPalette } from '../theme'

export default function LoginPage() {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        px: 2,
      }}
    >
      <Paper
        elevation={0}
        className="page-enter"
        sx={{
          p: { xs: 4, sm: 6 },
          maxWidth: 420,
          width: '100%',
          textAlign: 'center',
          borderRadius: 4,
          background: 'rgba(255,255,255,0.65)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: `1px solid ${alpha(berryPalette.rose, 0.35)}`,
          boxShadow: `0 20px 60px ${alpha(berryPalette.berry, 0.18)}`,
        }}
      >
        {/* Иконка */}
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${berryPalette.rose}, ${berryPalette.berry})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
            boxShadow: `0 8px 24px ${alpha(berryPalette.raspberry, 0.4)}`,
          }}
        >
          <FlightTakeoffIcon sx={{ color: '#fff', fontSize: 30 }} />
        </Box>

        <Typography variant="h4" gutterBottom fontWeight={700} color="primary.dark">
          Track the Ticket
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Monitor flight prices automatically
        </Typography>

        <Divider sx={{ mb: 3, opacity: 0.4 }} />

        {/* FE-08: подключится к Cognito в модуле Auth */}
        <Button
          variant="contained"
          size="large"
          startIcon={<GoogleIcon />}
          fullWidth
          disabled
          sx={{ mb: 2 }}
        >
          Sign in with Google
        </Button>

        <Typography variant="caption" color="text.secondary">
          Auth integration coming in Module 3
        </Typography>
      </Paper>
    </Box>
  )
}
