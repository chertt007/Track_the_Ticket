import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export type Language = 'ru' | 'en'

interface SettingsState {
  language: Language
}

const LANG_KEY = 'ttt_language'

const savedLanguage = localStorage.getItem(LANG_KEY) as Language | null

const initialState: SettingsState = {
  language: savedLanguage ?? 'en',
}

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setLanguage: (state, action: PayloadAction<Language>) => {
      state.language = action.payload
      localStorage.setItem(LANG_KEY, action.payload)
    },
  },
})

export const { setLanguage } = settingsSlice.actions
export default settingsSlice.reducer
