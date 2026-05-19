import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { skyPalette } from '../theme'

export const settingsStyles = {
  iconButton: {
    opacity: 0.85,
  } as SxProps<Theme>,

  menuPaper: {
    mt: 1,
    minWidth: 220,
    borderRadius: 3,
    background: 'rgba(255,255,255,0.92)',
    backdropFilter: 'blur(20px)',
    border: `1px solid ${alpha(skyPalette.brightSky, 0.3)}`,
    boxShadow: `0 8px 32px ${alpha(skyPalette.deepSky, 0.18)}`,
  } as SxProps<Theme>,

  headerBox: {
    px: 2,
    py: 1.5,
  } as SxProps<Theme>,

  divider: {
    opacity: 0.4,
  } as SxProps<Theme>,

  sectionBox: {
    px: 2,
    py: 1.5,
  } as SxProps<Theme>,

  langLabelRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    mb: 1,
  } as SxProps<Theme>,

  langIcon: {
    fontSize: 16,
    color: 'text.secondary',
  } as SxProps<Theme>,

  toggleButton: {
    fontWeight: 600,
    fontSize: '0.8rem',
  } as SxProps<Theme>,

  telegramRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    mb: 1.25,
  } as SxProps<Theme>,

  telegramIcon: {
    fontSize: 18,
    color: '#229ED9',
  } as SxProps<Theme>,

  telegramButton: {
    fontWeight: 600,
    fontSize: '0.8rem',
    textTransform: 'none',
  } as SxProps<Theme>,
}
