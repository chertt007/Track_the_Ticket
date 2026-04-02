import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface AuthUser {
  sub: string
  email: string
  picture?: string   // Google profile photo URL, comes from Cognito id-token claims
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

    // Dev-only: bypass Cognito for local UI testing.
    // Token is a structurally valid JWT (header.payload.sig) so the API can parse
    // it and return a proper 401 instead of crashing on malformed input.
    mockLogin: (state) => {
      state.isAuthenticated = true
      state.loading = false
      state.user = { sub: 'dev-user-001', email: 'dev@tracktheticket.local' }
      state.token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6Im1vY2sta2lkLTAwMSIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXYtdXNlci0wMDEiLCJlbWFpbCI6ImRldkB0cmFja3RoZXRpY2tldC5sb2NhbCIsImV4cCI6OTk5OTk5OTk5OX0.mock-signature'
    },
  },
})

export const { setAuth, clearAuth, setAuthLoading, mockLogin } = authSlice.actions
export default authSlice.reducer
