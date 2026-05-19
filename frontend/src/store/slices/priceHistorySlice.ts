import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { getPriceHistory, type PriceHistoryApiItem } from '../../api'
import type { PriceHistory } from '../../types'

function mapItem(raw: PriceHistoryApiItem): PriceHistory {
  return {
    id:             raw.id,
    subscriptionId: raw.subscription_id,
    price:          raw.amount ?? 0,
    currency:       raw.currency ?? 'RUB',
    s3Key:          null,
    checkedAt:      raw.checked_at,
    status:         raw.status,
  }
}

export const fetchPriceHistory = createAsyncThunk<PriceHistory[], string>(
  'priceHistory/fetch',
  async (subId: string) => {
    const items = await getPriceHistory(subId)
    return items.map(mapItem)
  },
)

interface PriceHistoryState {
  bySubId: Record<string, PriceHistory[]>
  loadingId: string | null
  error: string | null
}

const initialState: PriceHistoryState = {
  bySubId:   {},
  loadingId: null,
  error:     null,
}

const priceHistorySlice = createSlice({
  name: 'priceHistory',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPriceHistory.pending, (state, action) => {
        state.loadingId = action.meta.arg
        state.error     = null
      })
      .addCase(fetchPriceHistory.fulfilled, (state, action) => {
        state.bySubId[action.meta.arg] = action.payload
        state.loadingId = null
      })
      .addCase(fetchPriceHistory.rejected, (state, action) => {
        state.loadingId = null
        state.error     = action.error.message ?? 'Failed to load price history'
      })
  },
})

export default priceHistorySlice.reducer
