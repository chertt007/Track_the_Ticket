import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { skyPalette } from '../theme'

export const layoutStyles = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  } as SxProps<Theme>,

  toolbar: {
    py: { xs: 0.5, sm: 1 },
  } as SxProps<Theme>,

  logoBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    cursor: 'pointer',
    flexGrow: 1,
  } as SxProps<Theme>,

  logoText: {
    fontWeight: 700,
    fontSize: { xs: '1rem', sm: '1.2rem' },
    letterSpacing: '-0.01em',
  } as SxProps<Theme>,

  logoIcon: {
    fontSize: { xs: 22, sm: 26 },
  } as SxProps<Theme>,

  navButton: (isActive: boolean): SxProps<Theme> => ({
    fontWeight: isActive ? 700 : 400,
    opacity: isActive ? 1 : 0.8,
    borderBottom: isActive ? '2px solid rgba(255,255,255,0.8)' : '2px solid transparent',
    borderRadius: 0,
    px: 1.5,
    fontSize: { xs: '0.85rem', sm: '0.95rem' },
  }),

  avatar: {
    width: 30,
    height: 30,
    fontSize: '0.8rem',
    fontWeight: 700,
    ml: 1,
    background: alpha(skyPalette.brightSky, 0.35),
    color: '#fff',
    border: '1px solid rgba(255,255,255,0.3)',
  } as SxProps<Theme>,

  signOutButton: {
    ml: 0.5,
    opacity: 0.85,
    fontSize: { xs: '0.8rem', sm: '0.9rem' },
    '&:hover': { opacity: 1 },
  } as SxProps<Theme>,

  langToggle: {
    ml: 0.5,
    minWidth: 0,
    px: 1,
    fontSize: '0.8rem',
    fontWeight: 700,
    letterSpacing: '0.05em',
    opacity: 0.85,
    '&:hover': { opacity: 1, background: 'rgba(255,255,255,0.12)' },
  } as SxProps<Theme>,

  main: {
    flexGrow: 1,
    py: { xs: 3, sm: 4, md: 5 },
    px: { xs: 2, sm: 3 },
  } as SxProps<Theme>,

  // ── Animated cloud layer inside AppBar ──────────────────────────────────────
  cloudLayer: {
    position: 'absolute',
    inset: 0,
    overflow: 'hidden',
    pointerEvents: 'none',
    zIndex: 0,
  } as SxProps<Theme>,

  // Cloud shape: pill base + two bumps via ::before / ::after.
  // Params: width(px), height(px), top(%), drift duration(s), animation delay(s)
  cloud: (width: number, height: number, top: string, duration: number, delay: number): SxProps<Theme> => ({
    position: 'absolute',
    top,
    left: 0,
    width:  `${width}px`,
    height: `${height}px`,
    background: 'rgba(255,255,255,0.38)',
    borderRadius: `${height}px`,
    animation: `cloudDrift ${duration}s linear ${delay}s infinite`,
    '&::before': {
      content: '""',
      background: 'rgba(255,255,255,0.38)',
      position: 'absolute',
      borderRadius: '50%',
      top: '-55%',
      left: '12%',
      width: '48%',
      height: '145%',
    },
    '&::after': {
      content: '""',
      background: 'rgba(255,255,255,0.38)',
      position: 'absolute',
      borderRadius: '50%',
      top: '-38%',
      right: '14%',
      width: '38%',
      height: '125%',
    },
  }),
}
