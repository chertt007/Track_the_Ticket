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

  // ── Last check (price + screenshot thumbnail) ──────────────────────────
  lastCheckBox: {
    display: 'flex',
    flexDirection: { xs: 'row', md: 'row' },
    alignItems: 'center',
    gap: 1.5,
    px: { xs: 0, md: 2 },
    minWidth: { xs: 'auto', md: 220 },
    flexShrink: 0,
  } as SxProps<Theme>,

  priceBox: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
  } as SxProps<Theme>,

  priceText: {
    fontWeight: 700,
    color: berryPalette.berry,
    fontSize: { xs: '1rem', sm: '1.1rem' },
    lineHeight: 1.2,
    whiteSpace: 'nowrap',
  } as SxProps<Theme>,

  pricePlaceholder: {
    color: alpha(berryPalette.berry, 0.45),
    fontStyle: 'italic',
    fontSize: '0.85rem',
  } as SxProps<Theme>,

  thumbnailButton: {
    p: 0,
    borderRadius: 2,
    overflow: 'hidden',
    border: `1px solid ${alpha(berryPalette.rose, 0.5)}`,
    boxShadow: `0 4px 14px ${alpha(berryPalette.berry, 0.15)}`,
    transition: 'transform 0.18s ease, box-shadow 0.18s ease',
    '&:hover': {
      transform: 'scale(1.03)',
      boxShadow: `0 8px 22px ${alpha(berryPalette.berry, 0.25)}`,
    },
  } as SxProps<Theme>,

  thumbnailImg: {
    display: 'block',
    width: { xs: 96, sm: 120, md: 140 },
    height: { xs: 64, sm: 80, md: 92 },
    objectFit: 'cover',
  } as SxProps<Theme>,

  // ── Lightbox (full-screen screenshot preview) ──────────────────────────
  lightboxPaper: {
    background: 'transparent',
    boxShadow: 'none',
    overflow: 'visible',
    m: { xs: 1, sm: 2 },
    maxWidth: '95vw',
    maxHeight: '95vh',
  } as SxProps<Theme>,

  lightboxBackdrop: {
    background: alpha(berryPalette.berry, 0.7),
    backdropFilter: 'blur(8px)',
  } as SxProps<Theme>,

  lightboxContent: {
    position: 'relative',
    p: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  } as SxProps<Theme>,

  lightboxImg: {
    display: 'block',
    maxWidth: '95vw',
    maxHeight: '90vh',
    width: 'auto',
    height: 'auto',
    borderRadius: 12,
    boxShadow: `0 20px 60px ${alpha(berryPalette.berry, 0.45)}`,
    cursor: 'zoom-out',
  } as SxProps<Theme>,

  lightboxCloseButton: {
    position: 'absolute',
    top: { xs: 8, sm: 12 },
    right: { xs: 8, sm: 12 },
    color: '#fff',
    background: alpha('#000', 0.4),
    backdropFilter: 'blur(6px)',
    '&:hover': {
      background: alpha('#000', 0.6),
    },
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

  deleteButton: {
    color: alpha(berryPalette.raspberry, 0.45),
    transition: 'all 0.2s ease',
    '&:hover': {
      color: berryPalette.raspberry,
      background: alpha(berryPalette.raspberry, 0.08),
    },
  } as SxProps<Theme>,

  actionBox: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 0.5,
    flexShrink: 0,
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

  // ── Delete confirm dialog ──────────────────────────────────────────────
  dialogPaper: {
    borderRadius: 4,
    background: 'rgba(255,255,255,0.92)',
    backdropFilter: 'blur(24px)',
    border: `1px solid ${alpha(berryPalette.rose, 0.3)}`,
    boxShadow: `0 20px 60px ${alpha(berryPalette.berry, 0.2)}`,
  } as SxProps<Theme>,

  dialogTitleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.5,
    pb: 1,
  } as SxProps<Theme>,

  dialogIconCircle: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: `linear-gradient(135deg, ${alpha(berryPalette.raspberry, 0.9)}, ${berryPalette.berry})`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    color: '#fff',
  } as SxProps<Theme>,

  dialogActions: {
    px: 3,
    pb: 2.5,
    gap: 1,
  } as SxProps<Theme>,

  dialogCancelButton: {
    color: berryPalette.berry,
    borderRadius: 2,
    textTransform: 'none',
    fontWeight: 600,
  } as SxProps<Theme>,

  dialogDeleteButton: {
    borderRadius: 2,
    textTransform: 'none',
    fontWeight: 600,
    background: `linear-gradient(135deg, ${alpha(berryPalette.raspberry, 0.95)}, ${berryPalette.berry})`,
    boxShadow: `0 6px 20px ${alpha(berryPalette.berry, 0.35)}`,
    '&:hover': {
      background: `linear-gradient(135deg, ${berryPalette.raspberry}, ${berryPalette.berry})`,
      boxShadow: `0 8px 24px ${alpha(berryPalette.berry, 0.45)}`,
    },
  } as SxProps<Theme>,
}
