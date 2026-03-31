import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import SearchOffIcon from '@mui/icons-material/SearchOff'
import AddIcon from '@mui/icons-material/Add'
import { useAppSelector } from '../hooks'
import { useT } from '../hooks/useT'
import SubscriptionCard from '../components/SubscriptionCard'
import AddSubscriptionModal from '../components/AddSubscriptionModal'
import { dashboardStyles as s } from './DashboardPage.styles'

export default function DashboardPage() {
  const t = useT()
  const subscriptions = useAppSelector(st => st.subscriptions.items)
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <Box className="page-enter">
      {/* Header */}
      <Box sx={s.headerRow}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="primary.dark">
            {t('mySubscriptions')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={s.subtitleText}>
            {subscriptions.length > 0
              ? `${subscriptions.length} ${subscriptions.length === 1 ? 'subscription' : 'subscriptions'}`
              : t('noSubscriptionsHint')}
          </Typography>
        </Box>

        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setModalOpen(true)} sx={s.addButton}>
          {t('addSubscription')}
        </Button>
      </Box>

      {/* Subscription list */}
      {subscriptions.length === 0 ? (
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
