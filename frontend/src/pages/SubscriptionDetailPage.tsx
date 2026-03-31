import { useParams } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export default function SubscriptionDetailPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Subscription #{id}
      </Typography>
      <Typography variant="body1" color="text.secondary">
        {/* FE-06: инфо о рейсе, 7-дневный график цен, скриншоты — будет реализовано */}
        Subscription detail content coming soon...
      </Typography>
    </Box>
  )
}
