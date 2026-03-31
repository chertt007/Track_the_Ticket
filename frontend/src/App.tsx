import { BrowserRouter } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

// Must be imported before any Amplify auth calls
import './config/amplify'

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
          {/* Resolves Amplify session and sets up Hub listener */}
          <AuthProvider>
            <AppRouter />
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  )
}

export default App
