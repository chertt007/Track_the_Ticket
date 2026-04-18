// subscriptionsSlice — real API, no mock data
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { Subscription } from '../../types'
import { apiClient, createSubscription, type CreateSubscriptionPayload } from '../../api'

// ── API response type (snake_case from FastAPI) ───────────────────────────────

interface SubscriptionApiResponse {
  id: number
  source_url: string
  status: string
  origin_iata: string | null
  destination_iata: string | null
  departure_date: string | null
  departure_time: string | null
  flight_number: string | null
  airline: string | null
  baggage_info: string | null
  is_active: boolean
  last_checked_at: string | null
  last_notified_at: string | null
}

// ── Mapping: API snake_case → frontend camelCase ──────────────────────────────

function mapSubscription(raw: SubscriptionApiResponse): Subscription {
  return {
    id:              String(raw.id),
    flightNumber:    raw.flight_number  ?? '—',
    airline:         raw.airline        ?? '—',
    originIata:      raw.origin_iata    ?? '???',
    destinationIata: raw.destination_iata ?? '???',
    departureDate:   raw.departure_date ?? '—',
    departureTime:   raw.departure_time?.slice(0, 5) ?? '—', // "08:30:00" → "08:30"
    baggageInfo:     raw.baggage_info   ?? '—',
    sourceUrl:       raw.source_url,
    isActive:        raw.is_active,
    lastCheckedAt:   raw.last_checked_at,
    lastPrice:       null, // fetched separately via GET /subscriptions/{id}/prices
    currency:        'RUB',
    screenshotUrl:   undefined,
  }
}

// ── Async thunk ───────────────────────────────────────────────────────────────

export const fetchSubscriptions = createAsyncThunk<Subscription[]>(
  'subscriptions/fetchAll',
  async () => {
    const response = await apiClient.get<SubscriptionApiResponse[]>('/subscriptions')
    return response.data.map(mapSubscription)
  },
)

export const createSubscriptionApi = createAsyncThunk<Subscription, CreateSubscriptionPayload>(
  'subscriptions/createApi',
  async (payload: CreateSubscriptionPayload) => {
    const raw = await createSubscription(payload)
    return mapSubscription(raw)
  },
)
export interface CheckResult {
  price: number
  currency: string
  flight_number: string
  checked_at: string
  screenshot_b64: string | null
}

export const checkSubscriptionApi = createAsyncThunk<
  { id: string; result: CheckResult },
  string
>(
  'subscriptions/checkApi',
  async (id: string) => {
    const { data } = await apiClient.post<CheckResult>(`/subscriptions/${id}/check`)
    return { id, result: data }
  },
)

export const deleteSubscriptionApi = createAsyncThunk<string, string>(
  'subscriptions/deleteApi',
  async (id: string) => {
    await apiClient.delete(`/subscriptions/${id}`)
    return id
  },
)

// ── Slice ─────────────────────────────────────────────────────────────────────

type FetchStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

interface SubscriptionsState {
  items: Subscription[]
  status: FetchStatus  // tracks fetch lifecycle — prevents duplicate requests
  loading: boolean
  error: string | null
  checkingId: string | null
}

const initialState: SubscriptionsState = {
  items:      [],
  status:     'idle',
  loading:    false,
  error:      null,
  checkingId: null,
}

const subscriptionsSlice = createSlice({
  name: 'subscriptions',
  initialState,
  reducers: {
    // Optimistic add — real subscription comes back on next fetchSubscriptions
    addSubscription: (state, action: PayloadAction<{ url: string }>) => {
      const newSub: Subscription = {
        id:              `pending-${Date.now()}`,
        flightNumber:    '—',
        airline:         '—',
        originIata:      '???',
        destinationIata: '???',
        departureDate:   '—',
        departureTime:   '—',
        baggageInfo:     '—',
        sourceUrl:       action.payload.url,
        isActive:        true,
        lastCheckedAt:   null,
        lastPrice:       null,
        currency:        'RUB',
      }
      state.items.unshift(newSub)
    },

    setCheckingId: (state, action: PayloadAction<string | null>) => {
      state.checkingId = action.payload
    },

    toggleActive: (state, action: PayloadAction<string>) => {
      const sub = state.items.find(s => s.id === action.payload)
      if (sub) sub.isActive = !sub.isActive
    },

    removeSubscription: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(s => s.id !== action.payload)
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchSubscriptions.pending, (state) => {
        state.status  = 'loading'
        state.loading = true
        state.error   = null
      })
      .addCase(fetchSubscriptions.fulfilled, (state, action) => {
        state.status  = 'succeeded'
        state.loading = false
        state.items   = action.payload
      })
      .addCase(fetchSubscriptions.rejected, (state, action) => {
        state.status  = 'failed'
        state.loading = false
        state.error   = action.error.message ?? 'Failed to load subscriptions'
      })
      .addCase(deleteSubscriptionApi.fulfilled, (state, action) => {
        state.items = state.items.filter(s => s.id !== action.payload)
      })
      .addCase(createSubscriptionApi.fulfilled, (state, action) => {
        state.items.unshift(action.payload)
      })
      .addCase(checkSubscriptionApi.fulfilled, (state, action) => {
        const { id, result } = action.payload
        const sub = state.items.find(s => s.id === id)
        if (sub) {
          sub.lastPrice = result.price
          sub.currency = result.currency
          sub.lastCheckedAt = result.checked_at
          if (result.screenshot_b64) {
            sub.screenshotUrl = `data:image/png;base64,${result.screenshot_b64}`
          }
        }
        state.checkingId = null
      })
  },
})

export const { addSubscription, setCheckingId, toggleActive, removeSubscription } =
  subscriptionsSlice.actions
export default subscriptionsSlice.reducer
