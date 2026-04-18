import type { PriceHistory } from '../types'

// Returns an ISO string for N days ago at a fixed morning time
function daysAgo(n: number, hour = 10): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  d.setHours(hour, 0, 0, 0)
  return d.toISOString()
}

// Mock price history — 7 data points per subscription over the last 7 days.
// Prices are intentionally non-monotone to make the chart interesting.
// Will be replaced by real API data in FE-07.
export const mockPriceHistory: Record<string, PriceHistory[]> = {
  'sub-001': [
    {
      id: 'ph-001-1', subscriptionId: 'sub-001',
      price: 44500, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(6), status: 'ok',
    },
    {
      id: 'ph-001-2', subscriptionId: 'sub-001',
      price: 43200, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(5), status: 'ok',
    },
    {
      id: 'ph-001-3', subscriptionId: 'sub-001',
      price: 45800, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(4), status: 'ok',
    },
    {
      id: 'ph-001-4', subscriptionId: 'sub-001',
      price: 46200, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(3), status: 'ok',
    },
    {
      id: 'ph-001-5', subscriptionId: 'sub-001',
      price: 43900, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(2), status: 'ok',
    },
    {
      id: 'ph-001-6', subscriptionId: 'sub-001',
      price: 41800, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(1), status: 'ok',
    },
    {
      id: 'ph-001-7', subscriptionId: 'sub-001',
      price: 42500, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(0), status: 'ok',
    },
  ],

  'sub-002': [
    {
      id: 'ph-002-1', subscriptionId: 'sub-002',
      price: 31200, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(6), status: 'ok',
    },
    {
      id: 'ph-002-2', subscriptionId: 'sub-002',
      price: 30500, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(5), status: 'ok',
    },
    {
      id: 'ph-002-3', subscriptionId: 'sub-002',
      price: 29800, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(4), status: 'ok',
    },
    {
      id: 'ph-002-4', subscriptionId: 'sub-002',
      price: 31500, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(3), status: 'failed',
    },
    {
      id: 'ph-002-5', subscriptionId: 'sub-002',
      price: 30100, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(2), status: 'ok',
    },
    {
      id: 'ph-002-6', subscriptionId: 'sub-002',
      price: 29400, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(1), status: 'ok',
    },
    {
      id: 'ph-002-7', subscriptionId: 'sub-002',
      price: 28900, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(0), status: 'ok',
    },
  ],

  'sub-003': [
    {
      id: 'ph-003-1', subscriptionId: 'sub-003',
      price: 58900, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(6), status: 'ok',
    },
    {
      id: 'ph-003-2', subscriptionId: 'sub-003',
      price: 60400, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(5), status: 'ok',
    },
    {
      id: 'ph-003-3', subscriptionId: 'sub-003',
      price: 62100, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(4), status: 'ok',
    },
    {
      id: 'ph-003-4', subscriptionId: 'sub-003',
      price: 61500, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(3), status: 'ok',
    },
    {
      id: 'ph-003-5', subscriptionId: 'sub-003',
      price: 63000, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(2), status: 'ok',
    },
    {
      id: 'ph-003-6', subscriptionId: 'sub-003',
      price: 61800, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(1), status: 'ok',
    },
    {
      id: 'ph-003-7', subscriptionId: 'sub-003',
      price: 61200, currency: 'RUB', s3Key: null,
      checkedAt: daysAgo(0), status: 'ok',
    },
  ],
}
