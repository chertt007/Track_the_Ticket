import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import CircularProgress from '@mui/material/CircularProgress'
import SearchOffIcon from '@mui/icons-material/SearchOff'
import AddIcon from '@mui/icons-material/Add'
import { useAppSelector, useAppDispatch } from '../hooks'
import { useT } from '../hooks/useT'
import { useLocale } from '../hooks/useLocale'
import { fetchSubscriptions } from '../store/slices/subscriptionsSlice'
import SubscriptionCard from '../components/SubscriptionCard'
import AddSubscriptionModal from '../components/AddSubscriptionModal'
import { dashboardStyles as s } from './DashboardPage.styles'

/** Russian plural rules: 1 → one, 2-4 → few, 5+ → many */
function ruPlural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 19) return `${n} ${many}`
  if (mod10 === 1) return `${n} ${one}`
  if (mod10 >= 2 && mod10 <= 4) return `${n} ${few}`
  return `${n} ${many}`
}

export default function DashboardPage() {
  const t = useT()
  const locale = useLocale()
  const dispatch = useAppDispatch()
  const subscriptions = useAppSelector(st => st.subscriptions.items)
  const loading = useAppSelector(st => st.subscriptions.loading)
  const error = useAppSelector(st => st.subscriptions.error)
  const [modalOpen, setModalOpen] = useState(false)

  // Fetch real subscriptions from API on mount
  useEffect(() => {
    dispatch(fetchSubscriptions())
  }, [dispatch])

  const subscriptionCount = locale === 'ru-RU'
    ? ruPlural(subscriptions.length, t('subscriptionOne'), t('subscriptionFew'), t('subscriptionMany'))
    : `${subscriptions.length} ${subscriptions.length === 1 ? t('subscriptionOne') : t('subscriptionFew')}`

  return (
    <Box className="page-enter">
      {/* Header */}
      <Box sx={s.headerRow}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="primary.dark">
            {t('mySubscriptions')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={s.subtitleText}>
            {subscriptions.length > 0 ? subscriptionCount : t('noSubscriptionsHint')}
          </Typography>
        </Box>

        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setModalOpen(true)} sx={s.addButton}>
          {t('addSubscription')}
        </Button>
      </Box>

      {/* API error banner — shown when GET /subscriptions fails */}
      {error && (
        <Box sx={s.errorBanner}>
          <Typography variant="body2" sx={s.errorText}>
            API error: {error}
          </Typography>
        </Box>
      )}

      {/* Subscription list */}
      {loading ? (
        <Box sx={s.loadingBox}>
          <CircularProgress />
        </Box>
      ) : subscriptions.length === 0 ? (
        <Box sx={s.emptyState}>
          <SearchOffIcon sx={s.emptyIcon} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('noSubscriptions')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={s.emptyHint}>
            {t('noSubscriptionsHint')}
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setModalOpen(true)}>
            {t('addSubscription')}
          </Button>
        </Box>
      ) : (
        <Stack spacing={2}>
          {subscriptions.map(sub => (
            <SubscriptionCard key={sub.id} subscription={sub} />
          ))}
        </Stack>
      )}

      {/* Add subscription modal */}
      <AddSubscriptionModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </Box>
  )
}
