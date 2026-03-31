// Domain types

export interface Subscription {
  id: string
  flightNumber: string
  airline: string
  originIata: string
  destinationIata: string
  departureDate: string
  departureTime: string
  baggageInfo: string
  sourceUrl: string
  isActive: boolean
  checkFrequency: number
  lastCheckedAt: string | null
  // mock fields (заменятся реальными данными в FE-07)
  mockScreenshotUrl?: string
  lastPrice: number | null
  currency: string
}

export interface PriceHistory {
  id: string
  subscriptionId: string
  price: number
  currency: string
  s3Key: string | null
  checkedAt: string
  status: 'ok' | 'failed' | 'suspicious'
}

export interface User {
  id: string
  email: string
  telegramId: string | null
}
