import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Subscription } from '../../types'

// Mock data — will be replaced by real API calls in FE-07
const mockSubscriptions: Subscription[] = [
  {
    id: 'sub-001',
    flightNumber: 'SU 1234',
    airline: 'Aeroflot',
    originIata: 'SVO',
    destinationIata: 'DXB',
    departureDate: '2026-05-15',
    departureTime: '08:30',
    baggageInfo: '1 × 23 kg',
    sourceUrl: 'https://www.aviasales.ru/search/SVO1505DXB1',
    isActive: true,
    checkFrequency: 3,
    lastCheckedAt: '2026-03-31T10:00:00Z',
    mockScreenshotUrl: 'https://placehold.co/320x180/9B1B5A/white?text=₽+42,500',
    lastPrice: 42500,
    currency: 'RUB',
  },
  {
    id: 'sub-002',
    flightNumber: 'TK 789',
    airline: 'Turkish Airlines',
    originIata: 'LED',
    destinationIata: 'IST',
    departureDate: '2026-04-02',
    departureTime: '14:15',
    baggageInfo: '1 × 20 kg',
    sourceUrl: 'https://www.aviasales.ru/search/LED0204IST1',
    isActive: true,
    checkFrequency: 3,
    lastCheckedAt: '2026-03-31T09:30:00Z',
    mockScreenshotUrl: 'https://placehold.co/320x180/D63384/white?text=₽+28,900',
    lastPrice: 28900,
    currency: 'RUB',
  },
  {
    id: 'sub-003',
    flightNumber: 'VY 456',
    airline: 'Vueling',
    originIata: 'SVO',
    destinationIata: 'BCN',
    departureDate: '2026-05-10',
    departureTime: '11:45',
    baggageInfo: 'Hand luggage only',
    sourceUrl: 'https://www.aviasales.ru/search/SVO1005BCN1',
    isActive: false,
    checkFrequency: 6,
    lastCheckedAt: null,
    mockScreenshotUrl: 'https://placehold.co/320x180/5C0A34/white?text=₽+61,200',
    lastPrice: 61200,
    currency: 'RUB',
  },
]

interface SubscriptionsState {
  items: Subscription[]
  loading: boolean
  checkingId: string | null  // id of the subscription currently being checked
}

const initialState: SubscriptionsState = {
  items: mockSubscriptions,
  loading: false,
  checkingId: null,
}

const subscriptionsSlice = createSlice({
  name: 'subscriptions',
  initialState,
  reducers: {
    addSubscription: (state, action: PayloadAction<{ url: string }>) => {
      const newSub: Subscription = {
        id: `sub-${Date.now()}`,
        flightNumber: '—',
        airline: '—',
        originIata: '???',
        destinationIata: '???',
        departureDate: '—',
        departureTime: '—',
        baggageInfo: '—',
        sourceUrl: action.payload.url,
        isActive: true,
        checkFrequency: 3,
        lastCheckedAt: null,
        mockScreenshotUrl: 'https://placehold.co/320x180/FF85A1/white?text=Pending...',
        lastPrice: null,
        currency: 'RUB',
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
})

export const { addSubscription, setCheckingId, toggleActive, removeSubscription } =
  subscriptionsSlice.actions
export default subscriptionsSlice.reducer
