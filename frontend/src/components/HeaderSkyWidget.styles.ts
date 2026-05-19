import type { SxProps, Theme } from '@mui/material'

export const skyWidgetStyles = {
  container: {
    position: 'relative',
    width: 58,
    height: 28,
    display: { xs: 'none', md: 'block' },
    flexShrink: 0,
    mx: 0.5,
  } as SxProps<Theme>,

  sun: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: 'sunCycle 12s ease-in-out infinite',
  } as SxProps<Theme>,

  cloud: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0,
    animation: 'cloudCycle 12s ease-in-out infinite',
  } as SxProps<Theme>,

  plane: {
    position: 'absolute',
    top: '50%',
    left: 0,
    opacity: 0,
    animation: 'planeFly 12s linear infinite',
  } as SxProps<Theme>,

  sunIcon: {
    color: '#FFD54F',
    fontSize: 20,
    filter: 'drop-shadow(0 0 4px rgba(255,213,79,0.6))',
  } as SxProps<Theme>,

  cloudIcon: {
    color: 'rgba(255,255,255,0.88)',
    fontSize: 20,
  } as SxProps<Theme>,

  planeIcon: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 15,
  } as SxProps<Theme>,
}
