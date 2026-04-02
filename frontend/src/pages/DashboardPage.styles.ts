import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const dashboardStyles = {
  pageBox: {
    // page-enter анимация применяется через className
  } as SxProps<Theme>,

  headerRow: {
    display: 'flex',
    alignItems: { xs: 'flex-start', sm: 'center' },
    justifyContent: 'space-between',
    flexDirection: { xs: 'column', sm: 'row' },
    gap: 2,
    mb: 4,
  } as SxProps<Theme>,

  subtitleText: {
    mt: 0.5,
  } as SxProps<Theme>,

  addButton: {
    flexShrink: 0,
  } as SxProps<Theme>,

  emptyState: {
    textAlign: 'center',
    py: 10,
    borderRadius: 4,
    border: `2px dashed ${alpha(berryPalette.rose, 0.4)}`,
    background: alpha(berryPalette.blush, 0.3),
  } as SxProps<Theme>,

  emptyIcon: {
    fontSize: 56,
    color: alpha(berryPalette.raspberry, 0.3),
    mb: 2,
  } as SxProps<Theme>,

  emptyHint: {
    mb: 3,
  } as SxProps<Theme>,

  loadingBox: {
    display: 'flex',
    justifyContent: 'center',
    mt: 8,
  } as SxProps<Theme>,

  errorBanner: {
    mb: 2,
    p: 2,
    bgcolor: 'error.light',
    borderRadius: 2,
  } as SxProps<Theme>,

  errorText: {
    color: 'error.contrastText',
  } as SxProps<Theme>,
}
