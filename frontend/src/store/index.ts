import { configureStore } from '@reduxjs/toolkit'

export const store = configureStore({
  reducer: {
    // slices will be added here as we build each feature
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
