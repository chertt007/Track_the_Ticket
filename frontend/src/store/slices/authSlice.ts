import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface AuthUser {
  sub: string
  email: string
}

interface AuthState {
  isAuthenticated: boolean
  loading: boolean         // true while Amplify is checking the session on startup
  user: AuthUser | null
  token: string | null     // raw JWT id-token, used for API Authorization header in FE-07
}

const initialState: AuthState = {
  isAuthenticated: false,
  loading: true,           // start as true — useAuth resolves it on mount
  user: null,
  token: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setAuth: (state, action: PayloadAction<{ user: AuthUser; token: string }>) => {
      state.isAuthenticated = true
      state.loading = false
      state.user = action.payload.user
      state.token = action.payload.token
    },

    clearAuth: (state) => {
      state.isAuthenticated = false
      state.loading = false
      state.user = null
      state.token = null
    },

    setAuthLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },

    // Dev-only: bypass Cognito for local UI testing
    mockLogin: (state) => {
      state.isAuthenticated = true
      state.loading = false
      state.user = { sub: 'dev-user-001', email: 'dev@tracktheticket.local' }
      state.token = 'mock-jwt-token'
    },
  },
})

export const { setAuth, clearAuth, setAuthLoading, mockLogin } = authSlice.actions
export default authSlice.reducer
