import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Paper from '@mui/material/Paper'
import Divider from '@mui/material/Divider'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import GoogleIcon from '@mui/icons-material/Google'
import { loginStyles as s } from './LoginPage.styles'

export default function LoginPage() {
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
          Monitor flight prices automatically
        </Typography>

        <Divider sx={s.divider} />

        {/* FE-08: подключится к Cognito в модуле Auth */}
        <Button variant="contained" size="large" startIcon={<GoogleIcon />} fullWidth disabled sx={s.googleButton}>
          Sign in with Google
        </Button>

        <Typography variant="caption" color="text.secondary">
          Auth integration coming in Module 3
        </Typography>
      </Paper>
    </Box>
  )
}
