import { configureStore } from '@reduxjs/toolkit'
import subscriptionsReducer from './slices/subscriptionsSlice'
import settingsReducer from './slices/settingsSlice'
import authReducer from './slices/authSlice'
import telegramReducer from './slices/telegramSlice'
import priceHistoryReducer from './slices/priceHistorySlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    subscriptions: subscriptionsReducer,
    settings: settingsReducer,
    telegram: telegramReducer,
    priceHistory: priceHistoryReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
