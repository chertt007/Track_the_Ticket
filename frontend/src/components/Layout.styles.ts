import type { SxProps, Theme } from '@mui/material'

export const layoutStyles = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  } as SxProps<Theme>,

  toolbar: {
    py: { xs: 0.5, sm: 1 },
  } as SxProps<Theme>,

  logoBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    cursor: 'pointer',
    flexGrow: 1,
  } as SxProps<Theme>,

  logoText: {
    fontWeight: 700,
    fontSize: { xs: '1rem', sm: '1.2rem' },
    letterSpacing: '-0.01em',
  } as SxProps<Theme>,

  logoIcon: {
    fontSize: { xs: 22, sm: 26 },
  } as SxProps<Theme>,

  navButton: (isActive: boolean): SxProps<Theme> => ({
    fontWeight: isActive ? 700 : 400,
    opacity: isActive ? 1 : 0.8,
    borderBottom: isActive ? '2px solid rgba(255,255,255,0.8)' : '2px solid transparent',
    borderRadius: 0,
    px: 1.5,
    fontSize: { xs: '0.85rem', sm: '0.95rem' },
  }),

  loginButton: {
    ml: 1,
    opacity: 0.85,
    fontSize: { xs: '0.85rem', sm: '0.95rem' },
  } as SxProps<Theme>,

  main: {
    flexGrow: 1,
    py: { xs: 3, sm: 4, md: 5 },
    px: { xs: 2, sm: 3 },
  } as SxProps<Theme>,
}
