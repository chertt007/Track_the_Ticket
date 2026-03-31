import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const screenshotStyles = {
  wrapper: {
    position: 'relative',
    width: { xs: '100%', sm: 200, md: 240 },
    borderRadius: 3,
    overflow: 'hidden',
    cursor: 'pointer',
    border: `1px solid ${alpha(berryPalette.rose, 0.3)}`,
    boxShadow: `0 4px 16px ${alpha(berryPalette.berry, 0.1)}`,
    flexShrink: 0,
    '&:hover .overlay': { opacity: 1 },
    '&:hover img': { transform: 'scale(1.04)' },
  } as SxProps<Theme>,

  image: {
    width: '100%',
    height: { xs: 100, sm: 120 },
    objectFit: 'cover',
    display: 'block',
    transition: 'transform 0.3s ease',
  } as SxProps<Theme>,

  overlay: {
    position: 'absolute',
    inset: 0,
    background: alpha(berryPalette.burgundy, 0.55),
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0,
    transition: 'opacity 0.25s ease',
    gap: 1,
  } as SxProps<Theme>,

  priceBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    background: `linear-gradient(to top, ${alpha(berryPalette.burgundy, 0.85)}, transparent)`,
    px: 1.5,
    py: 0.75,
  } as SxProps<Theme>,

  dialogPaper: {
    background: 'rgba(30,0,20,0.92)',
    backdropFilter: 'blur(20px)',
    borderRadius: 3,
    overflow: 'hidden',
  } as SxProps<Theme>,

  dialogInner: {
    position: 'relative',
  } as SxProps<Theme>,

  closeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    color: '#fff',
    background: alpha(berryPalette.burgundy, 0.6),
    zIndex: 1,
    '&:hover': { background: berryPalette.burgundy },
  } as SxProps<Theme>,

  fullImage: {
    width: '100%',
    maxHeight: '80vh',
    objectFit: 'contain',
    display: 'block',
  } as SxProps<Theme>,
}
