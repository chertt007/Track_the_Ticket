import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { skyPalette } from '../theme'

export const cardStyles = {
  card: (isActive: boolean): SxProps<Theme> => ({
    display: 'flex',
    flexDirection: { xs: 'column', md: 'row' },
    alignItems: { xs: 'stretch', md: 'center' },
    gap: { xs: 2, md: 0 },
    p: { xs: 2, sm: 3 },
    borderLeft: `4px solid ${isActive ? skyPalette.sky : alpha(skyPalette.brightSky, 0.4)}`,
    opacity: isActive ? 1 : 0.7,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: `0 8px 32px ${alpha(skyPalette.deepSky, 0.15)}`,
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
    color: skyPalette.deepSky,
    fontSize: { xs: '1rem', sm: '1.1rem' },
    lineHeight: 1.2,
    whiteSpace: 'nowrap',
  } as SxProps<Theme>,

  pricePlaceholder: {
    color: alpha(skyPalette.deepSky, 0.45),
    fontStyle: 'italic',
    fontSize: '0.85rem',
  } as SxProps<Theme>,

  thumbnailButton: {
    p: 0,
    borderRadius: 2,
    overflow: 'hidden',
    border: `1px solid ${alpha(skyPalette.brightSky, 0.5)}`,
    boxShadow: `0 4px 14px ${alpha(skyPalette.deepSky, 0.15)}`,
    transition: 'transform 0.18s ease, box-shadow 0.18s ease',
    '&:hover': {
      transform: 'scale(1.03)',
      boxShadow: `0 8px 22px ${alpha(skyPalette.deepSky, 0.25)}`,
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
    background: alpha(skyPalette.twilight, 0.75),
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
    boxShadow: `0 20px 60px ${alpha(skyPalette.twilight, 0.5)}`,
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
    color: skyPalette.sky,
    background: alpha(skyPalette.brightSky, 0.15),
    border: `1px solid ${alpha(skyPalette.sky, 0.25)}`,
    transition: 'all 0.2s ease',
    '&:hover': {
      background: alpha(skyPalette.sky, 0.12),
      transform: 'rotate(180deg)',
    },
  } as SxProps<Theme>,

  deleteButton: {
    color: alpha(skyPalette.sky, 0.45),
    transition: 'all 0.2s ease',
    '&:hover': {
      color: skyPalette.sky,
      background: alpha(skyPalette.sky, 0.08),
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
    color: skyPalette.sky,
  } as SxProps<Theme>,

  takeoffIcon: {
    color: skyPalette.sky,
    fontSize: 20,
  } as SxProps<Theme>,

  landIcon: {
    color: skyPalette.deepSky,
    fontSize: 20,
  } as SxProps<Theme>,

  // ── Delete confirm dialog ──────────────────────────────────────────────
  dialogPaper: {
    borderRadius: 4,
    background: 'rgba(255,255,255,0.92)',
    backdropFilter: 'blur(24px)',
    border: `1px solid ${alpha(skyPalette.brightSky, 0.3)}`,
    boxShadow: `0 20px 60px ${alpha(skyPalette.deepSky, 0.2)}`,
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
    background: `linear-gradient(135deg, ${alpha(skyPalette.sky, 0.9)}, ${skyPalette.deepSky})`,
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
    color: skyPalette.deepSky,
    borderRadius: 2,
    textTransform: 'none',
    fontWeight: 600,
  } as SxProps<Theme>,

  dialogDeleteButton: {
    borderRadius: 2,
    textTransform: 'none',
    fontWeight: 600,
    background: `linear-gradient(135deg, ${alpha(skyPalette.sky, 0.95)}, ${skyPalette.deepSky})`,
    boxShadow: `0 6px 20px ${alpha(skyPalette.deepSky, 0.35)}`,
    '&:hover': {
      background: `linear-gradient(135deg, ${skyPalette.sky}, ${skyPalette.deepSky})`,
      boxShadow: `0 8px 24px ${alpha(skyPalette.deepSky, 0.45)}`,
    },
  } as SxProps<Theme>,
}
