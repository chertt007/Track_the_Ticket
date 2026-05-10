import axios from 'axios'
import { signOut } from 'firebase/auth'
import { auth } from '@/config/firebase'
import { store } from '@/store'
import { clearAuth } from '@/store/slices/authSlice'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(async (config) => {
  // Firebase SDK caches and rotates tokens for us — getIdToken() is cheap
  // when the token is fresh and refreshes it automatically when expired.
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Sign the user out so the AuthGuard sends them to /login.
      await signOut(auth).catch(() => undefined)
      store.dispatch(clearAuth())
    }
    return Promise.reject(error)
  }
)

// ── Parse ─────────────────────────────────────────────────────────────────────

export const parseTicketUrl = async (sourceUrl: string) => {
  const { data } = await apiClient.post(
    '/parse',
    { source_url: sourceUrl },
    { timeout: 60_000 },
  )
  return data
}

// ── Subscriptions ─────────────────────────────────────────────────────────────

export interface CreateSubscriptionPayload {
  source_url: string
  origin_iata: string
  destination_iata: string
  departure_date: string        // "YYYY-MM-DD"
  departure_time: string | null
  flight_number: string | null
  airline: string | null
  airline_iata: string | null
  airline_domain: string | null
  baggage_info: string | null
}

export const createSubscription = async (payload: CreateSubscriptionPayload) => {
  const { data } = await apiClient.post('/subscriptions', payload)
  return data
}
