import { configureStore } from '@reduxjs/toolkit'
import subscriptionsReducer from './slices/subscriptionsSlice'
import settingsReducer from './slices/settingsSlice'
import authReducer from './slices/authSlice'
import telegramReducer from './slices/telegramSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    subscriptions: subscriptionsReducer,
    settings: settingsReducer,
    telegram: telegramReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
