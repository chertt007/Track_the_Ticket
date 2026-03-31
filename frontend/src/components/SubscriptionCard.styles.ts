import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const cardStyles = {
  card: (isActive: boolean): SxProps<Theme> => ({
    display: 'flex',
    flexDirection: { xs: 'column', md: 'row' },
    alignItems: { xs: 'stretch', md: 'center' },
    gap: { xs: 2, md: 0 },
    p: { xs: 2, sm: 3 },
    borderLeft: `4px solid ${isActive ? berryPalette.raspberry : alpha(berryPalette.rose, 0.4)}`,
    opacity: isActive ? 1 : 0.7,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: `0 8px 32px ${alpha(berryPalette.berry, 0.15)}`,
    },
  }),

  infoBox: {
    flexGrow: 1,
    minWidth: 0,
  } as SxProps<Theme>,

  routeRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    mb: 1,
    flexWrap: 'wrap',
  } as SxProps<Theme>,

  detailsRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 2,
  } as SxProps<Theme>,

  baggageBox: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: 0.5,
  } as SxProps<Theme>,

  metaText: {
    mt: 0.5,
    display: 'block',
  } as SxProps<Theme>,

  screenshotBox: {
    mx: { xs: 0, md: 2 },
    flexShrink: 0,
  } as SxProps<Theme>,

  actionBox: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0,
  } as SxProps<Theme>,

  checkButton: {
    color: berryPalette.raspberry,
    background: alpha(berryPalette.rose, 0.15),
    border: `1px solid ${alpha(berryPalette.raspberry, 0.25)}`,
    transition: 'all 0.2s ease',
    '&:hover': {
      background: alpha(berryPalette.raspberry, 0.12),
      transform: 'rotate(180deg)',
    },
  } as SxProps<Theme>,

  chip: {
    ml: 'auto',
    fontSize: '0.7rem',
  } as SxProps<Theme>,

  spinner: {
    color: berryPalette.raspberry,
  } as SxProps<Theme>,

  takeoffIcon: {
    color: berryPalette.raspberry,
    fontSize: 20,
  } as SxProps<Theme>,

  landIcon: {
    color: berryPalette.berry,
    fontSize: 20,
  } as SxProps<Theme>,

  luggageIcon: {
    fontSize: 14,
    color: 'text.secondary',
    mb: 0.2,
  } as SxProps<Theme>,
}
