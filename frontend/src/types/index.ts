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
  lastPrice: number | null
  currency: string
  screenshotUrl?: string
}

export interface PriceHistory {
  id: string
  subscriptionId: string
  price: number
  currency: string
  s3Key: string | null
  checkedAt: string
  status: 'ok' | 'failed' | 'suspicious'
  // mock field — will be replaced by presigned S3 URL from API in FE-07
  mockScreenshotUrl?: string
}

export interface User {
  id: string
  email: string
  telegramId: string | null
}

// TicketPreview will be added back once the backend Playwright parsing is wired up
