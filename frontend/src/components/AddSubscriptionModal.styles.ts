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
    flexShrink: 0,
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

  // ── Confirmation step ────────────────────────────────────────────────────────

  confirmCard: {
    borderRadius: 3,
    background: alpha(berryPalette.rose, 0.06),
    border: `1px solid ${alpha(berryPalette.rose, 0.18)}`,
    p: 2.5,
    mb: 2.5,
  } as SxProps<Theme>,

  routeRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    mb: 2.5,
  } as SxProps<Theme>,

  routeAirportBlock: {
    flex: 1,
    textAlign: 'center' as const,
  } as SxProps<Theme>,

  routeAirportCode: {
    fontSize: { xs: '2rem', sm: '2.25rem' },
    fontWeight: 800,
    color: berryPalette.berry,
    letterSpacing: '-1px',
    lineHeight: 1,
  } as SxProps<Theme>,

  routeArrowBlock: {
    flex: '0 0 auto',
    display: 'flex',
    alignItems: 'center',
    px: 1,
  } as SxProps<Theme>,

  routeArrowIcon: {
    color: alpha(berryPalette.raspberry, 0.45),
    fontSize: 28,
  } as SxProps<Theme>,

  infoGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: 1.5,
  } as SxProps<Theme>,

  infoItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0.3,
  } as SxProps<Theme>,

  infoLabel: {
    fontSize: '0.68rem',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.07em',
    color: 'text.disabled',
  } as SxProps<Theme>,

  infoValue: {
    fontSize: '0.875rem',
    fontWeight: 600,
    color: 'text.primary',
  } as SxProps<Theme>,

  infoPriceValue: {
    fontSize: '0.9rem',
    fontWeight: 700,
    color: berryPalette.raspberry,
  } as SxProps<Theme>,

  baggageSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: 1.5,
    mt: 0.5,
  } as SxProps<Theme>,

  baggageLabelRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
  } as SxProps<Theme>,

  baggageIcon: {
    fontSize: 20,
    color: 'text.secondary',
  } as SxProps<Theme>,

  baggageToggleGroup: {
    gap: 1,
    '& .MuiToggleButtonGroup-grouped': {
      borderRadius: '20px !important',
      border: `1px solid ${alpha(berryPalette.rose, 0.4)} !important`,
      px: 3,
      py: 0.75,
      fontWeight: 600,
      fontSize: '0.875rem',
      textTransform: 'none',
      minWidth: 80,
      color: berryPalette.berry,
      '&.Mui-selected': {
        background: `linear-gradient(135deg, ${berryPalette.rose}, ${berryPalette.raspberry})`,
        color: '#fff',
        borderColor: 'transparent !important',
      },
      '&:hover:not(.Mui-selected)': {
        background: alpha(berryPalette.rose, 0.1),
      },
    },
  } as SxProps<Theme>,
}
