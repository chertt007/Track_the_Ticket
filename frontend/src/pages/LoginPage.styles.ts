import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const loginStyles = {
  pageBox: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    px: 2,
  } as SxProps<Theme>,

  paper: {
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
  } as SxProps<Theme>,

  iconCircle: {
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
  } as SxProps<Theme>,

  icon: {
    color: '#fff',
    fontSize: 30,
  } as SxProps<Theme>,

  subtitle: {
    mb: 4,
  } as SxProps<Theme>,

  divider: {
    mb: 3,
    opacity: 0.4,
  } as SxProps<Theme>,

  googleButton: {
    mb: 2,
  } as SxProps<Theme>,
}
