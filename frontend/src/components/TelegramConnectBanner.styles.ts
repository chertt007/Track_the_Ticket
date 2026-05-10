import { SxProps, Theme } from '@mui/material/styles'

export const telegramBannerStyles = {
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: 2,
    p: { xs: 2, sm: 2.5 },
    mb: 3,
    borderRadius: 2,
    background: 'linear-gradient(135deg, rgba(34,158,217,0.08) 0%, rgba(26,123,170,0.12) 100%)',
    border: '1px solid',
    borderColor: 'rgba(34,158,217,0.25)',
  } satisfies SxProps<Theme>,

  iconCircle: {
    flexShrink: 0,
    width: 44,
    height: 44,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #229ED9 0%, #1A7BAA 100%)',
    color: '#fff',
  } satisfies SxProps<Theme>,

  textColumn: {
    flex: 1,
    minWidth: 0,
  } satisfies SxProps<Theme>,

  title: {
    fontWeight: 700,
    color: 'primary.dark',
    fontSize: { xs: '0.95rem', sm: '1rem' },
  } satisfies SxProps<Theme>,

  subtitle: {
    color: 'text.secondary',
    fontSize: { xs: '0.8rem', sm: '0.85rem' },
    mt: 0.25,
  } satisfies SxProps<Theme>,

  button: {
    flexShrink: 0,
    background: 'linear-gradient(135deg, #229ED9 0%, #1A7BAA 100%)',
    color: '#fff',
    fontWeight: 600,
    '&:hover': {
      background: 'linear-gradient(135deg, #1A7BAA 0%, #146289 100%)',
    },
  } satisfies SxProps<Theme>,
}
