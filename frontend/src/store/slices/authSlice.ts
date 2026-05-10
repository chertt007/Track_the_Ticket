import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface AuthUser {
  uid: string
  email: string | null
  displayName: string | null
  photoURL: string | null
}

interface AuthState {
  // null = signed out, AuthUser = signed in. `loading` distinguishes
  // "definitely signed out" from "still resolving Firebase session on app start".
  user: AuthUser | null
  loading: boolean
}

const initialState: AuthState = {
  user: null,
  loading: true,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<AuthUser>) => {
      state.user = action.payload
      state.loading = false
    },

    clearAuth: (state) => {
      state.user = null
      state.loading = false
    },
  },
})

export const { setUser, clearAuth } = authSlice.actions
export default authSlice.reducer
