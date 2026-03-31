import { alpha, keyframes } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

const slideUp = keyframes`
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
`

export const installStyles = {
  banner: {
    position: 'fixed',
    bottom: { xs: 12, sm: 24 },
    left: '50%',
    transform: 'translateX(-50%)',
    zIndex: 1400,
    width: { xs: 'calc(100vw - 32px)', sm: 420 },
    borderRadius: 4,
    background: `linear-gradient(135deg, ${berryPalette.berry}, ${berryPalette.burgundy})`,
    boxShadow: `0 8px 32px ${alpha(berryPalette.burgundy, 0.5)}`,
    display: 'flex',
    alignItems: 'center',
    gap: 2,
    px: 2.5,
    py: 1.75,
    animation: `${slideUp} 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`,
  } as SxProps<Theme>,

  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 2.5,
    overflow: 'hidden',
    flexShrink: 0,
    border: '1.5px solid rgba(255,255,255,0.25)',
  } as SxProps<Theme>,

  textBox: {
    flexGrow: 1,
    minWidth: 0,
  } as SxProps<Theme>,

  installButton: {
    flexShrink: 0,
    background: 'rgba(255,255,255,0.18)',
    color: '#fff',
    border: '1px solid rgba(255,255,255,0.35)',
    fontWeight: 700,
    fontSize: '0.82rem',
    px: 2,
    py: 0.75,
    borderRadius: 2,
    backdropFilter: 'blur(8px)',
    '&:hover': {
      background: 'rgba(255,255,255,0.28)',
    },
    textTransform: 'none',
  } as SxProps<Theme>,

  closeButton: {
    color: 'rgba(255,255,255,0.7)',
    p: 0.5,
    flexShrink: 0,
    '&:hover': { color: '#fff', background: 'rgba(255,255,255,0.1)' },
  } as SxProps<Theme>,
}
