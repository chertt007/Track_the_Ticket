import { SxProps, Theme } from '@mui/material/styles'

export const telegramModalStyles = {
  paper: {
    p: { xs: 3, sm: 4 },
    minWidth: { xs: '90vw', sm: 420 },
    maxWidth: 480,
    borderRadius: 3,
    textAlign: 'center',
  } satisfies SxProps<Theme>,

  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #229ED9 0%, #1A7BAA 100%)',
    color: '#fff',
    mx: 'auto',
    mb: 2,
  } satisfies SxProps<Theme>,

  icon: {
    fontSize: 32,
  } satisfies SxProps<Theme>,

  title: {
    mb: 0.5,
  } satisfies SxProps<Theme>,

  subtitle: {
    mb: 3,
  } satisfies SxProps<Theme>,

  primaryButton: {
    background: 'linear-gradient(135deg, #229ED9 0%, #1A7BAA 100%)',
    color: '#fff',
    fontWeight: 600,
    py: 1.25,
    '&:hover': {
      background: 'linear-gradient(135deg, #1A7BAA 0%, #146289 100%)',
    },
  } satisfies SxProps<Theme>,

  expiryText: {
    mt: 2,
    color: 'text.secondary',
    fontSize: '0.85rem',
  } satisfies SxProps<Theme>,

  hint: {
    mt: 2,
    color: 'text.secondary',
    fontSize: '0.85rem',
  } satisfies SxProps<Theme>,

  waiting: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 1.25,
    mt: 2,
    color: 'text.secondary',
    fontSize: '0.85rem',
  } satisfies SxProps<Theme>,

  successRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 1,
    mb: 1,
    color: 'success.main',
    fontWeight: 600,
  } satisfies SxProps<Theme>,

  chatIdMono: {
    fontFamily: 'monospace',
    color: 'text.primary',
  } satisfies SxProps<Theme>,

  unlinkButton: {
    mt: 2,
  } satisfies SxProps<Theme>,

  errorAlert: {
    mb: 2,
  } satisfies SxProps<Theme>,

  loadingBox: {
    py: 4,
    display: 'flex',
    justifyContent: 'center',
  } satisfies SxProps<Theme>,
}
