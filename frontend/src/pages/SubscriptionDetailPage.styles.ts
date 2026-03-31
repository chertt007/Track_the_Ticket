import { alpha } from '@mui/material/styles'
import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

const glassCard: SxProps<Theme> = {
  borderRadius: 4,
  background: 'rgba(255,255,255,0.75)',
  backdropFilter: 'blur(16px)',
  border: `1px solid ${alpha(berryPalette.rose, 0.25)}`,
  boxShadow: `0 4px 24px ${alpha(berryPalette.berry, 0.08)}`,
  p: { xs: 2, sm: 3 },
  mb: 2.5,
}

export const detailStyles = {
  // ── Top bar ──────────────────────────────────────────────────────────────
  topBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.5,
    mb: 3,
  } as SxProps<Theme>,

  backButton: {
    color: 'primary.dark',
    '&:hover': { background: alpha(berryPalette.rose, 0.15) },
  } as SxProps<Theme>,

  routeTitle: {
    fontWeight: 700,
    color: 'primary.dark',
    letterSpacing: 1,
  } as SxProps<Theme>,

  // ── Flight info card ─────────────────────────────────────────────────────
  infoCard: {
    ...glassCard,
  } as SxProps<Theme>,

  sectionLabel: {
    fontWeight: 700,
    color: 'primary.dark',
    mb: 2,
  } as SxProps<Theme>,

  flightRouteRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.5,
    mb: 2.5,
    flexWrap: 'wrap' as const,
  } as SxProps<Theme>,

  iataText: {
    fontWeight: 800,
    fontSize: { xs: '1.6rem', sm: '2rem' },
    color: 'primary.dark',
    letterSpacing: 2,
  } as SxProps<Theme>,

  arrowText: {
    fontWeight: 700,
    fontSize: '1.4rem',
    color: 'text.secondary',
  } as SxProps<Theme>,

  statusChip: {
    ml: 'auto',
    fontWeight: 700,
  } as SxProps<Theme>,

  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
    gap: 2,
    mb: 2.5,
  } as SxProps<Theme>,

  detailItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 0.25,
  } as SxProps<Theme>,

  sourceLinkRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    pt: 1.5,
    borderTop: `1px solid ${alpha(berryPalette.rose, 0.2)}`,
  } as SxProps<Theme>,

  // ── Stats row ────────────────────────────────────────────────────────────
  statsRow: {
    display: 'grid',
    gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
    gap: 2,
    mb: 2.5,
  } as SxProps<Theme>,

  statCard: (accent: string): SxProps<Theme> => ({
    borderRadius: 3,
    background: `linear-gradient(135deg, ${alpha(accent, 0.12)}, ${alpha(accent, 0.06)})`,
    border: `1px solid ${alpha(accent, 0.25)}`,
    p: 2,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 0.5,
    textAlign: 'center',
  }),

  statValue: {
    fontWeight: 800,
    fontSize: { xs: '1.3rem', sm: '1.5rem' },
  } as SxProps<Theme>,

  // ── Price chart card ─────────────────────────────────────────────────────
  chartCard: {
    ...glassCard,
  } as SxProps<Theme>,

  chartWrapper: {
    mt: 2,
    mx: { xs: -1, sm: 0 },
  } as SxProps<Theme>,

  // ── Screenshot gallery card ──────────────────────────────────────────────
  galleryCard: {
    ...glassCard,
  } as SxProps<Theme>,

  galleryGrid: {
    display: 'grid',
    gridTemplateColumns: {
      xs: 'repeat(2, 1fr)',
      sm: 'repeat(3, 1fr)',
      md: 'repeat(4, 1fr)',
    },
    gap: 1.5,
    mt: 2,
  } as SxProps<Theme>,

  galleryItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 0.5,
  } as SxProps<Theme>,

  galleryDateRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 0.5,
  } as SxProps<Theme>,

  failedBadge: {
    background: alpha('#f44336', 0.12),
    color: '#c62828',
    border: `1px solid ${alpha('#f44336', 0.3)}`,
    borderRadius: 1,
    px: 0.75,
    py: 0.25,
    fontSize: '0.65rem',
    fontWeight: 700,
    lineHeight: 1.4,
  } as SxProps<Theme>,

  // ── Chart tooltip ────────────────────────────────────────────────────────
  chartTooltip: {
    background: 'rgba(255,255,255,0.95)',
    border: `1px solid ${berryPalette.rose}`,
    borderRadius: 2,
    px: 1.5,
    py: 1,
    boxShadow: `0 4px 16px ${alpha(berryPalette.berry, 0.15)}`,
  } as SxProps<Theme>,

  // ── Empty / not found states ─────────────────────────────────────────────
  notFound: {
    textAlign: 'center',
    py: 10,
  } as SxProps<Theme>,

  emptyChart: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: 200,
    color: 'text.secondary',
  } as SxProps<Theme>,
}
