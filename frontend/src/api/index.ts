import axios from 'axios'
import { store } from '@/store'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = store.getState().auth.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      store.dispatch({ type: 'auth/clearAuth' })
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
  check_frequency?: number
}

export const createSubscription = async (payload: CreateSubscriptionPayload) => {
  const { data } = await apiClient.post('/subscriptions', payload)
  return data
}
