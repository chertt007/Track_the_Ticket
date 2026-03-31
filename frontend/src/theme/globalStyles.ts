import { GlobalStyles as MuiGlobalStyles } from '@mui/material'

// Animated berry blobs background
const GlobalStyles = () =>
  MuiGlobalStyles({
    styles: {
      '*': { margin: 0, padding: 0, boxSizing: 'border-box' },
      '*::-webkit-scrollbar': { width: 6 },
      '*::-webkit-scrollbar-track': { background: 'rgba(255,255,255,0.1)' },
      '*::-webkit-scrollbar-thumb': {
        background: 'rgba(155, 27, 90, 0.4)',
        borderRadius: 3,
      },

      // Root background — soft pink-to-rose gradient
      'html, body, #root': {
        minHeight: '100vh',
        fontFamily: '"Poppins", "Roboto", sans-serif',
      },

      body: {
        background: 'linear-gradient(135deg, #FFF0F5 0%, #FFD6E7 30%, #FFADD0 60%, #F48FB1 100%)',
        backgroundAttachment: 'fixed',
        position: 'relative',
        overflow: 'hidden',
      },

      // Floating berry blobs — decorative blurred background shapes
      'body::before': {
        content: '""',
        position: 'fixed',
        top: '-20%',
        left: '-10%',
        width: '55vw',
        height: '55vw',
        borderRadius: '50%',
        background:
          'radial-gradient(circle, rgba(214,51,132,0.28) 0%, rgba(155,27,90,0.12) 60%, transparent 100%)',
        filter: 'blur(60px)',
        animation: 'blobDrift1 18s ease-in-out infinite',
        zIndex: 0,
      },
      'body::after': {
        content: '""',
        position: 'fixed',
        bottom: '-15%',
        right: '-10%',
        width: '60vw',
        height: '60vw',
        borderRadius: '50%',
        background:
          'radial-gradient(circle, rgba(92,10,52,0.22) 0%, rgba(214,51,132,0.1) 60%, transparent 100%)',
        filter: 'blur(70px)',
        animation: 'blobDrift2 22s ease-in-out infinite',
        zIndex: 0,
      },

      // Content sits above blobs
      '#root': { position: 'relative', zIndex: 1 },

      // Blob drift animations
      '@keyframes blobDrift1': {
        '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
        '33%': { transform: 'translate(5vw, 8vh) scale(1.08)' },
        '66%': { transform: 'translate(-3vw, 4vh) scale(0.95)' },
      },
      '@keyframes blobDrift2': {
        '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
        '33%': { transform: 'translate(-6vw, -5vh) scale(1.05)' },
        '66%': { transform: 'translate(4vw, -8vh) scale(0.97)' },
      },

      // Page transition fade-in
      '@keyframes fadeInUp': {
        from: { opacity: 0, transform: 'translateY(16px)' },
        to: { opacity: 1, transform: 'translateY(0)' },
      },
      '.page-enter': {
        animation: 'fadeInUp 0.35s ease forwards',
      },
    },
  })

export default GlobalStyles
