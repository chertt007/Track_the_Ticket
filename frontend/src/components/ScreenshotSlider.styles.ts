import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const sliderStyles = {
  // ── Loading / empty states ───────────────────────────────────────────────
  center: {
    display: 'flex',
    justifyContent: 'center',
    py: 3,
  } as SxProps<Theme>,

  // ── Main large image ─────────────────────────────────────────────────────
  mainWrapper: {
    position: 'relative',
    width: '100%',
    borderRadius: 3,
    overflow: 'hidden',
    cursor: 'pointer',
    border: `1px solid ${alpha(berryPalette.rose, 0.3)}`,
    boxShadow: `0 4px 20px ${alpha(berryPalette.berry, 0.12)}`,
    mb: 1,
    '&:hover .overlay': { opacity: 1 },
    '&:hover img': { transform: 'scale(1.02)' },
  } as SxProps<Theme>,

  mainImage: {
    width: '100%',
    height: { xs: 180, sm: 300 },
    objectFit: 'cover',
    display: 'block',
    transition: 'transform 0.3s ease',
  } as SxProps<Theme>,

  overlay: {
    position: 'absolute',
    inset: 0,
    background: alpha(berryPalette.burgundy, 0.45),
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 0.5,
    opacity: 0,
    transition: 'opacity 0.25s ease',
  } as SxProps<Theme>,

  // ── Metadata row (date + price) ──────────────────────────────────────────
  metaRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    mb: 1.5,
    px: 0.5,
  } as SxProps<Theme>,

  // ── Thumbnail nav row ────────────────────────────────────────────────────
  navRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 0.5,
  } as SxProps<Theme>,

  arrowBtn: {
    color: berryPalette.raspberry,
    flexShrink: 0,
    '&.Mui-disabled': { opacity: 0.25 },
    '&:hover': { background: alpha(berryPalette.rose, 0.15) },
  } as SxProps<Theme>,

  thumbnailStrip: {
    display: 'flex',
    gap: 1,
    overflowX: 'auto',
    flex: 1,
    py: 0.5,
    // Thin custom scrollbar
    scrollbarWidth: 'thin',
    '&::-webkit-scrollbar': { height: 4 },
    '&::-webkit-scrollbar-thumb': {
      background: alpha(berryPalette.rose, 0.4),
      borderRadius: 2,
    },
  } as SxProps<Theme>,

  thumbnail: (active: boolean): SxProps<Theme> => ({
    width: 72,
    height: 48,
    flexShrink: 0,
    borderRadius: 1.5,
    overflow: 'hidden',
    cursor: 'pointer',
    border: `2px solid ${active ? berryPalette.raspberry : alpha(berryPalette.rose, 0.3)}`,
    boxShadow: active ? `0 0 0 2px ${alpha(berryPalette.raspberry, 0.25)}` : 'none',
    opacity: active ? 1 : 0.55,
    transition: 'all 0.2s ease',
    '&:hover': {
      opacity: 1,
      borderColor: berryPalette.rose,
    },
  }),

  thumbImage: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block',
  } as SxProps<Theme>,

  // ── Lightbox ─────────────────────────────────────────────────────────────
  dialogPaper: {
    background: 'rgba(30,0,20,0.92)',
    backdropFilter: 'blur(20px)',
    borderRadius: 3,
    overflow: 'hidden',
  } as SxProps<Theme>,

  dialogInner: {
    position: 'relative',
  } as SxProps<Theme>,

  closeBtn: {
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
