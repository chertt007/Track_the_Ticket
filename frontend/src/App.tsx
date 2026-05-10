import { BrowserRouter } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

// Must be imported once before any auth calls — initializes Firebase app
import './config/firebase'

import { store } from './store'
import AppRouter from './pages/AppRouter'
import theme from './theme'
import GlobalStyles from './theme/globalStyles'
import AuthProvider from './components/AuthProvider'

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <GlobalStyles />
        <BrowserRouter>
          {/* Mirrors Firebase auth state into Redux */}
          <AuthProvider>
            <AppRouter />
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  )
}

export default App
