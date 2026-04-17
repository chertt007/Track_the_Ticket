import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  resolve: {
    alias: {
      '@': '/src',
    },
    // Prevent duplicate emotion/MUI instances which cause "createTheme is not a function"
    dedupe: ['@mui/material', '@mui/system', '@emotion/react', '@emotion/styled'],
  },
  // Force Vite to pre-bundle emotion together with MUI so they share a single
  // module instance. Without this, MUI chunks embed emotion internally while
  // direct app imports load it separately → two instances → runtime errors.
  optimizeDeps: {
    include: [
      '@emotion/react',
      '@emotion/styled',
      '@mui/material/styles',
      '@mui/material',
    ],
  },
})
