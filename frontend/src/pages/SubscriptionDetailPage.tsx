import { useParams, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import Button from '@mui/material/Button'
import Tooltip from '@mui/material/Tooltip'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import FlightLandIcon from '@mui/icons-material/FlightLand'
import LuggageIcon from '@mui/icons-material/Luggage'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ReferenceLine,
} from 'recharts'
import { useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import { useLocale } from '../hooks/useLocale'
import { mockPriceHistory } from '../mocks/priceHistory'
import ScreenshotPreview from '../components/ScreenshotPreview'
import { detailStyles as s } from './SubscriptionDetailPage.styles'
import { berryPalette } from '../theme'

// Custom recharts tooltip with berry styling
function PriceTooltip({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ value: number }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <Box sx={s.chartTooltip}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="body2" fontWeight={700} color="primary.dark">
        {payload[0].value.toLocaleString('ru-RU')} ₽
      </Typography>
    </Box>
  )
}

export default function SubscriptionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const t = useT()
  const locale = useLocale()

  const sub = useAppSelector(st => st.subscriptions.items.find(s => s.id === id))
  const history = id ? (mockPriceHistory[id] ?? []) : []

  // Subscription not found
  if (!sub) {
    return (
      <Box sx={s.notFound}>
        <Typography variant="h5" color="text.secondary" gutterBottom>
          {t('subscriptionNotFound')}
        </Typography>
        <Button variant="contained" onClick={() => navigate('/dashboard')} sx={{ mt: 2 }}>
          {t('backToDashboard')}
        </Button>
      </Box>
    )
  }

  // Compute stats from history (skip failed checks)
  const successPrices = history.filter(h => h.status === 'ok').map(h => h.price)
  const minPrice = successPrices.length ? Math.min(...successPrices) : null
  const maxPrice = successPrices.length ? Math.max(...successPrices) : null
  const currentPrice = sub.lastPrice

  // Prepare chart data
  const chartData = history.map(h => ({
    date: new Date(h.checkedAt).toLocaleDateString(locale, { month: 'short', day: 'numeric' }),
    price: h.status === 'ok' ? h.price : null,
  }))

  // Formatted departure date
  const formattedDeparture = sub.departureDate !== '—'
    ? new Date(sub.departureDate).toLocaleDateString(locale, {
        day: 'numeric', month: 'long', year: 'numeric',
      })
    : '—'

  return (
    <Box className="page-enter">
      {/* ── Back button + route header ──────────────────────────────────── */}
      <Box sx={s.topBar}>
        <Tooltip title={t('backToDashboard')}>
          <IconButton onClick={() => navigate('/dashboard')} sx={s.backButton}>
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <Typography variant="h5" sx={s.routeTitle}>
          {sub.originIata} → {sub.destinationIata}
        </Typography>
        <Chip
          label={sub.isActive ? t('active') : t('inactive')}
          size="small"
          color={sub.isActive ? 'primary' : 'default'}
          sx={s.statusChip}
        />
      </Box>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <Box sx={s.statsRow}>
        <Box sx={s.statCard(berryPalette.raspberry)}>
          <Typography variant="caption" color="text.secondary">{t('currentPrice')}</Typography>
          <Typography sx={{ ...s.statValue, color: berryPalette.raspberry }}>
            {currentPrice ? `${currentPrice.toLocaleString('ru-RU')} ₽` : '—'}
          </Typography>
        </Box>
        <Box sx={s.statCard(berryPalette.berry)}>
          <Typography variant="caption" color="text.secondary">{t('minPrice')}</Typography>
          <Typography sx={{ ...s.statValue, color: berryPalette.berry }}>
            {minPrice ? `${minPrice.toLocaleString('ru-RU')} ₽` : '—'}
          </Typography>
        </Box>
        <Box sx={s.statCard(berryPalette.burgundy)}>
          <Typography variant="caption" color="text.secondary">{t('maxPrice')}</Typography>
          <Typography sx={{ ...s.statValue, color: berryPalette.burgundy }}>
            {maxPrice ? `${maxPrice.toLocaleString('ru-RU')} ₽` : '—'}
          </Typography>
        </Box>
      </Box>

      {/* ── Flight info card ────────────────────────────────────────────── */}
      <Card elevation={0} sx={s.infoCard}>
        <Typography variant="h6" sx={s.sectionLabel}>{t('flightInfo')}</Typography>

        <Box sx={s.flightRouteRow}>
          <FlightTakeoffIcon sx={{ color: berryPalette.rose, fontSize: 28 }} />
          <Typography sx={s.iataText}>{sub.originIata}</Typography>
          <Typography sx={s.arrowText}>→</Typography>
          <FlightLandIcon sx={{ color: berryPalette.raspberry, fontSize: 28 }} />
          <Typography sx={s.iataText}>{sub.destinationIata}</Typography>
        </Box>

        <Box sx={s.detailsGrid}>
          <Box sx={s.detailItem}>
            <Typography variant="caption" color="text.secondary">{t('flight')}</Typography>
            <Typography variant="body2" fontWeight={600}>{sub.flightNumber}</Typography>
          </Box>
          <Box sx={s.detailItem}>
            <Typography variant="caption" color="text.secondary">{t('departure')}</Typography>
            <Typography variant="body2" fontWeight={600}>{formattedDeparture}</Typography>
          </Box>
          <Box sx={s.detailItem}>
            <Typography variant="caption" color="text.secondary">{t('departure')} (time)</Typography>
            <Typography variant="body2" fontWeight={600}>{sub.departureTime}</Typography>
          </Box>
          <Box sx={s.detailItem}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <LuggageIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">{t('baggage')}</Typography>
            </Box>
            <Typography variant="body2" fontWeight={600}>{sub.baggageInfo}</Typography>
          </Box>
          <Box sx={s.detailItem}>
            <Typography variant="caption" color="text.secondary">{t('checkFrequencyLabel')}</Typography>
            <Typography variant="body2" fontWeight={600}>{sub.checkFrequency}×</Typography>
          </Box>
          <Box sx={s.detailItem}>
            <Typography variant="caption" color="text.secondary">{t('lastChecked')}</Typography>
            <Typography variant="body2" fontWeight={600}>
              {sub.lastCheckedAt
                ? new Date(sub.lastCheckedAt).toLocaleString(locale, {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                  })
                : t('never')}
            </Typography>
          </Box>
        </Box>

        <Box sx={s.sourceLinkRow}>
          <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
            {t('sourceLink')}:
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: berryPalette.raspberry, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}
          >
            {sub.sourceUrl}
          </Typography>
          <Button
            size="small"
            variant="outlined"
            endIcon={<OpenInNewIcon sx={{ fontSize: 14 }} />}
            href={sub.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ flexShrink: 0, fontSize: '0.72rem', py: 0.25, px: 1 }}
          >
            {t('openLink')}
          </Button>
        </Box>
      </Card>

      {/* ── Price chart ─────────────────────────────────────────────────── */}
      <Card elevation={0} sx={s.chartCard}>
        <Typography variant="h6" sx={s.sectionLabel}>{t('priceHistory')}</Typography>

        {history.length === 0 ? (
          <Box sx={s.emptyChart}>
            <Typography variant="body2">{t('noPriceData')}</Typography>
          </Box>
        ) : (
          <Box sx={s.chartWrapper}>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="4 4" stroke="rgba(155,27,90,0.1)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#9e6070' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9e6070' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={v => `${(v / 1000).toFixed(0)}к`}
                  width={36}
                />
                <ChartTooltip content={<PriceTooltip />} />
                {minPrice && (
                  <ReferenceLine
                    y={minPrice}
                    stroke={berryPalette.berry}
                    strokeDasharray="3 3"
                    strokeOpacity={0.5}
                  />
                )}
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke={berryPalette.raspberry}
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#fff', stroke: berryPalette.raspberry, strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: berryPalette.raspberry }}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Card>

      {/* ── Screenshot gallery ──────────────────────────────────────────── */}
      <Card elevation={0} sx={s.galleryCard}>
        <Typography variant="h6" sx={s.sectionLabel}>{t('screenshots')}</Typography>

        {history.length === 0 ? (
          <Typography variant="body2" color="text.secondary">{t('noScreenshots')}</Typography>
        ) : (
          <Box sx={s.galleryGrid}>
            {history.map(h => (
              <Box key={h.id} sx={s.galleryItem}>
                <ScreenshotPreview
                  src={h.mockScreenshotUrl ?? 'https://placehold.co/320x180/9B1B5A/white?text=No+data'}
                />
                <Box sx={s.galleryDateRow}>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(h.checkedAt).toLocaleDateString(locale, { month: 'short', day: 'numeric' })}
                  </Typography>
                  {h.status !== 'ok' && (
                    <Box component="span" sx={s.failedBadge}>{t('statusFailed')}</Box>
                  )}
                </Box>
                {h.status === 'ok' && (
                  <Typography variant="caption" fontWeight={700} color="primary.dark">
                    {h.price.toLocaleString('ru-RU')} {h.currency}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        )}
      </Card>
    </Box>
  )
}
