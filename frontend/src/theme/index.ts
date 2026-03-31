import { createTheme, alpha } from '@mui/material/styles'

// ─── Ягодная палитра ──────────────────────────────────────────────────────────
export const berryPalette = {
  blush: '#FFD6E0',       // нежно-розовый (самый светлый)
  rose: '#FF85A1',        // розовый
  raspberry: '#D63384',   // малиновый / primary
  berry: '#9B1B5A',       // ягодный / primary dark
  burgundy: '#5C0A34',    // бордовый (самый тёмный)
  glassWhite: 'rgba(255, 255, 255, 0.15)',
  glassBorder: 'rgba(255, 255, 255, 0.25)',
}

const theme = createTheme({
  // ─── Mobile First breakpoints ──────────────────────────────────────────────
  breakpoints: {
    values: { xs: 0, sm: 600, md: 900, lg: 1200, xl: 1536 },
  },

  // ─── Палитра ───────────────────────────────────────────────────────────────
  palette: {
    mode: 'light',
    primary: {
      light: berryPalette.rose,
      main: berryPalette.raspberry,
      dark: berryPalette.berry,
      contrastText: '#fff',
    },
    secondary: {
      light: berryPalette.blush,
      main: berryPalette.rose,
      dark: berryPalette.raspberry,
      contrastText: '#5C0A34',
    },
    background: {
      default: 'transparent',
      paper: 'rgba(255, 255, 255, 0.55)',
    },
    text: {
      primary: '#3A0020',
      secondary: '#7A3050',
    },
    error: { main: '#E53935' },
    success: { main: '#2E7D32' },
  },

  // ─── Типографика — Poppins ─────────────────────────────────────────────────
  typography: {
    fontFamily: '"Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 700, letterSpacing: '-0.02em' },
    h2: { fontWeight: 700, letterSpacing: '-0.01em' },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { fontWeight: 600, textTransform: 'none', letterSpacing: '0.02em' },
    body1: { lineHeight: 1.7 },
    body2: { lineHeight: 1.6 },
  },

  // ─── Форма элементов ───────────────────────────────────────────────────────
  shape: { borderRadius: 16 },

  // ─── Тени ─────────────────────────────────────────────────────────────────
  shadows: [
    'none',
    `0 2px 8px ${alpha(berryPalette.berry, 0.08)}`,
    `0 4px 16px ${alpha(berryPalette.berry, 0.12)}`,
    `0 8px 24px ${alpha(berryPalette.berry, 0.15)}`,
    `0 12px 32px ${alpha(berryPalette.berry, 0.18)}`,
    `0 16px 40px ${alpha(berryPalette.berry, 0.2)}`,
    ...Array(19).fill(`0 16px 40px ${alpha(berryPalette.berry, 0.2)}`),
  ] as any,

  // ─── Компоненты ───────────────────────────────────────────────────────────
  components: {
    // AppBar — glassmorphism
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(135deg, ${alpha(berryPalette.burgundy, 0.85)} 0%, ${alpha(berryPalette.berry, 0.85)} 100%)`,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          boxShadow: `0 4px 24px ${alpha(berryPalette.burgundy, 0.25)}`,
          borderBottom: `1px solid ${berryPalette.glassBorder}`,
        },
      },
    },

    // Card — стеклянный эффект
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid ${berryPalette.glassBorder}`,
          borderRadius: 20,
          boxShadow: `0 8px 32px ${alpha(berryPalette.berry, 0.12)}`,
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: `0 12px 40px ${alpha(berryPalette.berry, 0.2)}`,
          },
        },
      },
    },

    // Paper — стеклянный эффект
    MuiPaper: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid ${berryPalette.glassBorder}`,
        },
      },
    },

    // Button — градиентные кнопки
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 50,
          padding: '10px 28px',
          fontSize: '0.95rem',
        },
        containedPrimary: {
          background: `linear-gradient(135deg, ${berryPalette.raspberry} 0%, ${berryPalette.berry} 100%)`,
          boxShadow: `0 4px 16px ${alpha(berryPalette.raspberry, 0.4)}`,
          '&:hover': {
            background: `linear-gradient(135deg, ${berryPalette.berry} 0%, ${berryPalette.burgundy} 100%)`,
            boxShadow: `0 6px 20px ${alpha(berryPalette.raspberry, 0.5)}`,
            transform: 'translateY(-1px)',
          },
        },
        outlinedPrimary: {
          borderColor: berryPalette.raspberry,
          color: berryPalette.raspberry,
          '&:hover': {
            borderColor: berryPalette.berry,
            background: alpha(berryPalette.raspberry, 0.06),
          },
        },
      },
    },

    // Chip
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 50,
          fontWeight: 600,
        },
        colorPrimary: {
          background: `linear-gradient(135deg, ${berryPalette.rose} 0%, ${berryPalette.raspberry} 100%)`,
          color: '#fff',
        },
      },
    },

    // TextField
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          background: 'rgba(255,255,255,0.7)',
          backdropFilter: 'blur(8px)',
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: berryPalette.raspberry,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: berryPalette.raspberry,
          },
        },
      },
    },

    // Tooltip
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          background: berryPalette.burgundy,
          borderRadius: 8,
          fontSize: '0.8rem',
        },
      },
    },

    // LinearProgress
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 4, height: 6 },
        barColorPrimary: {
          background: `linear-gradient(90deg, ${berryPalette.rose}, ${berryPalette.raspberry})`,
        },
      },
    },
  },
})

export default theme
