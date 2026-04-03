import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const modalStyles = {
  paper: {
    borderRadius: 4,
    background: 'rgba(255,255,255,0.85)',
    backdropFilter: 'blur(24px)',
    border: `1px solid ${alpha(berryPalette.rose, 0.3)}`,
    boxShadow: `0 20px 60px ${alpha(berryPalette.berry, 0.2)}`,
  } as SxProps<Theme>,

  titleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.5,
  } as SxProps<Theme>,

  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: `linear-gradient(135deg, ${berryPalette.rose}, ${berryPalette.raspberry})`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } as SxProps<Theme>,

  dialogTitle: {
    pb: 1,
  } as SxProps<Theme>,

  dialogContent: {
    pt: 1,
  } as SxProps<Theme>,

  hintText: {
    mb: 2,
  } as SxProps<Theme>,

  dialogActions: {
    px: 3,
    pb: 3,
    gap: 1,
  } as SxProps<Theme>,

  inputProps: {
    fontFamily: 'monospace',
    fontSize: '0.85rem',
  } as SxProps<Theme>,

  // Centered loading state
  parsingBox: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    py: 5,
  } as SxProps<Theme>,
}
