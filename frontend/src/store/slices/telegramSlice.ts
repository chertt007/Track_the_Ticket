import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import {
  getTelegramStatus,
  unlinkTelegram as apiUnlinkTelegram,
  type TelegramLinkToken,
} from '../../api'

interface TelegramState {
  // null while we have not yet fetched. Lets components distinguish
  // "not linked" from "we don't know yet" and avoid flashing the banner
  // before the first /telegram/status call resolves.
  linked: boolean | null
  chatIdMasked: string | null
  loading: boolean
  error: string | null
  // The most recently issued deep-link token, kept here so the modal can
  // show countdown / "open again" without owning the issue flow itself
  // (the issue + window.open dance lives in useTelegramConnect).
  pendingLink: TelegramLinkToken | null
}

const initialState: TelegramState = {
  linked: null,
  chatIdMasked: null,
  loading: false,
  error: null,
  pendingLink: null,
}

export const fetchTelegramStatus = createAsyncThunk(
  'telegram/fetchStatus',
  async () => getTelegramStatus(),
)

export const unlinkTelegramThunk = createAsyncThunk(
  'telegram/unlink',
  async () => {
    await apiUnlinkTelegram()
    return getTelegramStatus()
  },
)

const telegramSlice = createSlice({
  name: 'telegram',
  initialState,
  reducers: {
    // For optimistic UI when the polling sees `linked: true`.
    setLinked: (state, action: PayloadAction<{ linked: boolean; chatIdMasked: string | null }>) => {
      state.linked = action.payload.linked
      state.chatIdMasked = action.payload.chatIdMasked
    },
    setPendingLink: (state, action: PayloadAction<TelegramLinkToken | null>) => {
      state.pendingLink = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTelegramStatus.pending, (s) => { s.loading = true; s.error = null })
      .addCase(fetchTelegramStatus.fulfilled, (s, a) => {
        s.loading = false
        s.linked = a.payload.linked
        s.chatIdMasked = a.payload.chat_id_masked
      })
      .addCase(fetchTelegramStatus.rejected, (s, a) => {
        s.loading = false
        s.error = a.error.message ?? 'failed'
      })
      .addCase(unlinkTelegramThunk.fulfilled, (s, a) => {
        s.linked = a.payload.linked
        s.chatIdMasked = a.payload.chat_id_masked
        s.pendingLink = null
      })
  },
})

export const { setLinked, setPendingLink } = telegramSlice.actions
export default telegramSlice.reducer
