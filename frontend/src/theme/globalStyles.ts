import { GlobalStyles as MuiGlobalStyles } from '@mui/material'

// Animated sky background with drifting cloud shapes
const GlobalStyles = () =>
  MuiGlobalStyles({
    styles: {
      '*': { margin: 0, padding: 0, boxSizing: 'border-box' },
      '*::-webkit-scrollbar': { width: 6 },
      '*::-webkit-scrollbar-track': { background: 'rgba(255,255,255,0.1)' },
      '*::-webkit-scrollbar-thumb': {
        background: 'rgba(2,136,209,0.35)',
        borderRadius: 3,
      },

      'html, body, #root': {
        minHeight: '100vh',
        fontFamily: '"Poppins", "Roboto", sans-serif',
      },

      // Root background — sky gradient from bright blue at top to near-white horizon
      body: {
        background: 'linear-gradient(180deg, #81D4FA 0%, #B3E5FC 20%, #E1F5FE 55%, #F0F8FF 80%, #FAFCFF 100%)',
        backgroundAttachment: 'fixed',
        position: 'relative',
        overflowX: 'hidden',
      },

      // Soft cloud mass — top-left diffuse sky glow
      'body::before': {
        content: '""',
        position: 'fixed',
        top: '-15%',
        left: '-8%',
        width: '55vw',
        height: '55vw',
        borderRadius: '50%',
        background:
          'radial-gradient(circle, rgba(79,195,247,0.22) 0%, rgba(2,136,209,0.1) 55%, transparent 100%)',
        filter: 'blur(55px)',
        animation: 'skyDrift1 20s ease-in-out infinite',
        zIndex: 0,
      },
      // Soft cloud mass — bottom-right diffuse horizon glow
      'body::after': {
        content: '""',
        position: 'fixed',
        bottom: '-15%',
        right: '-8%',
        width: '60vw',
        height: '60vw',
        borderRadius: '50%',
        background:
          'radial-gradient(circle, rgba(1,87,155,0.15) 0%, rgba(79,195,247,0.07) 55%, transparent 100%)',
        filter: 'blur(65px)',
        animation: 'skyDrift2 25s ease-in-out infinite',
        zIndex: 0,
      },

      // Content sits above background layer
      '#root': { position: 'relative', zIndex: 1 },

      // Background cloud drift animations
      '@keyframes skyDrift1': {
        '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
        '33%':       { transform: 'translate(4vw, 6vh) scale(1.06)' },
        '66%':       { transform: 'translate(-3vw, 3vh) scale(0.96)' },
      },
      '@keyframes skyDrift2': {
        '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
        '33%':       { transform: 'translate(-5vw, -4vh) scale(1.04)' },
        '66%':       { transform: 'translate(3vw, -6vh) scale(0.98)' },
      },

      // Header cloud shapes drifting left → right
      '@keyframes cloudDrift': {
        '0%':   { transform: 'translateX(-220px) translateY(0px)' },
        '50%':  { transform: 'translateX(50vw) translateY(-3px)' },
        '100%': { transform: 'translateX(calc(100vw + 220px)) translateY(0px)' },
      },

      // HeaderSkyWidget — sun / cloud visibility cycle (12s)
      '@keyframes sunCycle': {
        '0%, 38%':    { opacity: 1,  transform: 'scale(1)' },
        '44%, 90%':   { opacity: 0,  transform: 'scale(0.7)' },
        '96%, 100%':  { opacity: 1,  transform: 'scale(1)' },
      },
      '@keyframes cloudCycle': {
        '0%, 38%':    { opacity: 0,  transform: 'scale(0.7)' },
        '44%, 90%':   { opacity: 1,  transform: 'scale(1)' },
        '96%, 100%':  { opacity: 0,  transform: 'scale(0.7)' },
      },

      // Airplane flies across the widget once per sun↔cloud swap
      '@keyframes planeFly': {
        '0%':    { transform: 'translateY(-50%) translateX(-60px)', opacity: 0 },
        '37%':   { transform: 'translateY(-50%) translateX(-60px)', opacity: 0 },
        '38%':   { transform: 'translateY(-50%) translateX(-60px)', opacity: 1 },
        '44%':   { transform: 'translateY(-50%) translateX(120px)',  opacity: 1 },
        '45%':   { transform: 'translateY(-50%) translateX(120px)',  opacity: 0 },
        '100%':  { transform: 'translateY(-50%) translateX(-60px)', opacity: 0 },
      },

      // Page transition fade-in
      '@keyframes fadeInUp': {
        from: { opacity: 0, transform: 'translateY(16px)' },
        to:   { opacity: 1, transform: 'translateY(0)' },
      },
      '.page-enter': {
        animation: 'fadeInUp 0.35s ease forwards',
      },
    },
  })

export default GlobalStyles
