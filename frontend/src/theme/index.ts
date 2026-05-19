import { createTheme, alpha } from '@mui/material/styles'

// ─── Sky palette ──────────────────────────────────────────────────────────────
export const skyPalette = {
  cloudWhite: '#E1F5FE',     // horizon / lightest sky
  brightSky:  '#4FC3F7',     // bright sky blue
  sky:        '#0288D1',     // primary main
  deepSky:    '#01579B',     // primary dark
  twilight:   '#002D62',     // deep navy / darkest
  glassWhite: 'rgba(255, 255, 255, 0.18)',
  glassBorder:'rgba(255, 255, 255, 0.32)',
}

const theme = createTheme({
  // ─── Mobile First breakpoints ──────────────────────────────────────────────
  breakpoints: {
    values: { xs: 0, sm: 600, md: 900, lg: 1200, xl: 1536 },
  },

  // ─── Palette ───────────────────────────────────────────────────────────────
  palette: {
    mode: 'light',
    primary: {
      light: skyPalette.brightSky,
      main:  skyPalette.sky,
      dark:  skyPalette.deepSky,
      contrastText: '#fff',
    },
    secondary: {
      light: skyPalette.cloudWhite,
      main:  skyPalette.brightSky,
      dark:  skyPalette.sky,
      contrastText: skyPalette.twilight,
    },
    background: {
      default: 'transparent',
      paper:   'rgba(255, 255, 255, 0.65)',
    },
    text: {
      primary:   '#0D2B4E',
      secondary: '#3E6B8C',
    },
    error:   { main: '#E53935' },
    success: { main: '#2E7D32' },
  },

  // ─── Typography — Poppins ──────────────────────────────────────────────────
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

  // ─── Shape ────────────────────────────────────────────────────────────────
  shape: { borderRadius: 16 },

  // ─── Shadows ──────────────────────────────────────────────────────────────
  shadows: [
    'none',
    `0 2px 8px ${alpha(skyPalette.deepSky, 0.08)}`,
    `0 4px 16px ${alpha(skyPalette.deepSky, 0.12)}`,
    `0 8px 24px ${alpha(skyPalette.deepSky, 0.15)}`,
    `0 12px 32px ${alpha(skyPalette.deepSky, 0.18)}`,
    `0 16px 40px ${alpha(skyPalette.deepSky, 0.2)}`,
    ...Array(19).fill(`0 16px 40px ${alpha(skyPalette.deepSky, 0.2)}`),
  ] as any,

  // ─── Component overrides ──────────────────────────────────────────────────
  components: {
    // AppBar — sky glassmorphism with overflow hidden for cloud layer
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(135deg, ${alpha(skyPalette.twilight, 0.92)} 0%, ${alpha(skyPalette.deepSky, 0.88)} 50%, ${alpha(skyPalette.sky, 0.85)} 100%)`,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          boxShadow: `0 4px 24px ${alpha(skyPalette.twilight, 0.3)}`,
          borderBottom: `1px solid ${skyPalette.glassBorder}`,
          overflow: 'hidden',
        },
      },
    },

    // Card — frosted-glass cloud card
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.68)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid ${alpha(skyPalette.brightSky, 0.25)}`,
          borderRadius: 20,
          boxShadow: `0 8px 32px ${alpha(skyPalette.deepSky, 0.1)}`,
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: `0 12px 40px ${alpha(skyPalette.deepSky, 0.18)}`,
          },
        },
      },
    },

    // Paper — frosted glass
    MuiPaper: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.68)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid ${alpha(skyPalette.brightSky, 0.2)}`,
        },
      },
    },

    // Button — sky gradient
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 50,
          padding: '10px 28px',
          fontSize: '0.95rem',
        },
        containedPrimary: {
          background: `linear-gradient(135deg, ${skyPalette.sky} 0%, ${skyPalette.deepSky} 100%)`,
          boxShadow: `0 4px 16px ${alpha(skyPalette.sky, 0.4)}`,
          '&:hover': {
            background: `linear-gradient(135deg, ${skyPalette.deepSky} 0%, ${skyPalette.twilight} 100%)`,
            boxShadow: `0 6px 20px ${alpha(skyPalette.sky, 0.5)}`,
            transform: 'translateY(-1px)',
          },
        },
        outlinedPrimary: {
          borderColor: skyPalette.sky,
          color: skyPalette.sky,
          '&:hover': {
            borderColor: skyPalette.deepSky,
            background: alpha(skyPalette.sky, 0.06),
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
          background: `linear-gradient(135deg, ${skyPalette.brightSky} 0%, ${skyPalette.sky} 100%)`,
          color: '#fff',
        },
      },
    },

    // TextField
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          background: 'rgba(255,255,255,0.78)',
          backdropFilter: 'blur(8px)',
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: skyPalette.sky,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: skyPalette.sky,
          },
        },
      },
    },

    // Tooltip
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          background: skyPalette.twilight,
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
          background: `linear-gradient(90deg, ${skyPalette.brightSky}, ${skyPalette.sky})`,
        },
      },
    },
  },
})

export default theme
