import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Fade from '@mui/material/Fade'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import LinkIcon from '@mui/icons-material/Link'
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff'
import LuggageIcon from '@mui/icons-material/Luggage'
import { useT } from '../hooks/useT'
import { parseTicketUrl } from '../api'
import { useAppDispatch } from '../hooks'
import { createSubscriptionApi } from '../store/slices/subscriptionsSlice'
import { modalStyles as s } from './AddSubscriptionModal.styles'

const AVIASALES_DOMAINS = ['aviasales.ru', 'aviasales.com', 'avs.io']

type Step = 'input' | 'parsing' | 'confirm'

interface ParsedData {
  source_url: string
  origin_iata: string | null
  destination_iata: string | null
  departure_date: string | null
  departure_time: string | null
  airline: string | null
  airline_iata: string | null
  price: number | null
  currency: string
  passengers: number | null
  is_round_trip: boolean
  baggage_info: string | null
  flight_number: string | null
  ticket_sign: string | null
}

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddSubscriptionModal({ open, onClose }: Props) {
  const t = useT()
  const dispatch = useAppDispatch()

  const [step, setStep] = useState<Step>('input')
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [needsBaggage, setNeedsBaggage] = useState<boolean | null>(null)

  const validate = (): string => {
    const trimmed = url.trim()
    if (!trimmed) return t('urlRequired')
    if (!trimmed.startsWith('http')) return t('urlInvalid')
    const isAviasales = AVIASALES_DOMAINS.some(d => trimmed.includes(d))
    if (!isAviasales) return t('urlNotAviasales')
    return ''
  }

  const handleCheck = () => {
    const err = validate()
    if (err) { setError(err); return }
    setStep('parsing')
    parseTicketUrl(url.trim())
      .then((data) => {
        setParsedData(data)
        setNeedsBaggage(null)
        setStep('confirm')
      })
      .catch((e) => {
        const msg = e?.response?.data?.detail ?? e?.message ?? t('urlInvalid')
        setError(msg)
        setStep('input')
      })
  }

  const handleConfirm = async () => {
    if (!parsedData) return
    await dispatch(createSubscriptionApi({
      source_url: parsedData.source_url,
      origin_iata: parsedData.origin_iata ?? '',
      destination_iata: parsedData.destination_iata ?? '',
      departure_date: parsedData.departure_date ?? '',
      departure_time: parsedData.departure_time ?? null,
      flight_number: parsedData.flight_number ?? null,
      airline: parsedData.airline ?? parsedData.airline_iata ?? null,
      airline_domain: null,
      baggage_info: needsBaggage ? 'with_baggage' : 'no_baggage',
    }))
    handleClose()
  }

  const handleBack = () => {
    setStep('input')
  }

  const handleClose = () => {
    if (step === 'parsing') return
    setStep('input')
    setUrl('')
    setError('')
    setParsedData(null)
    setNeedsBaggage(null)
    onClose()
  }

  const titleText =
    step === 'confirm' ? t('confirmTitle') :
    step === 'parsing' ? t('previewLoading') :
    t('addSubscriptionTitle')

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth PaperProps={{ sx: s.paper }}>
      <DialogTitle sx={s.dialogTitle}>
        <Box sx={s.titleRow}>
          <Box sx={s.iconCircle}>
            {step === 'confirm'
              ? <FlightTakeoffIcon sx={{ color: '#fff', fontSize: 18 }} />
              : <LinkIcon sx={{ color: '#fff', fontSize: 18 }} />
            }
          </Box>
          <Typography variant="h6" fontWeight={700} color="primary.dark">
            {titleText}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={s.dialogContent}>

        {/* ── Step: URL input ─────────────────────────────────────────── */}
        {step === 'input' && (
          <Fade in>
            <Box>
              <Typography variant="body2" color="text.secondary" sx={s.hintText}>
                {t('urlHint')}
              </Typography>
              <TextField
                fullWidth
                autoFocus
                label={t('urlLabel')}
                placeholder={t('urlPlaceholder')}
                value={url}
                onChange={e => { setUrl(e.target.value); setError('') }}
                error={!!error}
                helperText={error}
                onKeyDown={e => e.key === 'Enter' && handleCheck()}
                InputProps={{ sx: s.inputProps }}
              />
            </Box>
          </Fade>
        )}

        {/* ── Step: parsing ───────────────────────────────────────────── */}
        {step === 'parsing' && (
          <Fade in>
            <Box sx={s.parsingBox}>
              <CircularProgress size={44} thickness={3} color="primary" />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {t('previewLoading')}
              </Typography>
            </Box>
          </Fade>
        )}

        {/* ── Step: confirm ───────────────────────────────────────────── */}
        {step === 'confirm' && parsedData && (
          <Fade in>
            <Box>
              {/* Flight info card */}
              <Box sx={s.confirmCard}>

                {/* Route: ORIGIN → DEST */}
                <Box sx={s.routeRow}>
                  <Box sx={s.routeAirportBlock}>
                    <Typography sx={s.routeAirportCode}>
                      {parsedData.origin_iata ?? '—'}
                    </Typography>
                  </Box>
                  <Box sx={s.routeArrowBlock}>
                    <FlightTakeoffIcon sx={s.routeArrowIcon} />
                  </Box>
                  <Box sx={s.routeAirportBlock}>
                    <Typography sx={s.routeAirportCode}>
                      {parsedData.destination_iata ?? '—'}
                    </Typography>
                  </Box>
                </Box>

                {/* Details: airline / departure / price */}
                <Box sx={s.infoGrid}>
                  <Box sx={s.infoItem}>
                    <Typography sx={s.infoLabel}>{t('confirmAirline')}</Typography>
                    <Typography sx={s.infoValue}>
                      {parsedData.airline ?? parsedData.airline_iata ?? '—'}
                    </Typography>
                  </Box>
                  <Box sx={s.infoItem}>
                    <Typography sx={s.infoLabel}>{t('departure')}</Typography>
                    <Typography sx={s.infoValue}>
                      {parsedData.departure_date ?? '—'}
                      {parsedData.departure_time ? ` ${parsedData.departure_time}` : ''}
                    </Typography>
                  </Box>
                  <Box sx={s.infoItem}>
                    <Typography sx={s.infoLabel}>{t('confirmPrice')}</Typography>
                    <Typography sx={s.infoPriceValue}>
                      {parsedData.price != null
                        ? `${parsedData.price} ${parsedData.currency}`
                        : '—'}
                    </Typography>
                  </Box>
                </Box>

              </Box>

              {/* Baggage question */}
              <Divider sx={{ mb: 2 }} />
              <Box sx={s.baggageSection}>
                <Box sx={s.baggageLabelRow}>
                  <LuggageIcon sx={s.baggageIcon} />
                  <Typography variant="body2" fontWeight={600}>
                    {t('confirmBaggageQuestion')}
                  </Typography>
                </Box>
                <ToggleButtonGroup
                  exclusive
                  value={needsBaggage}
                  onChange={(_, val) => { if (val !== null) setNeedsBaggage(val) }}
                  sx={s.baggageToggleGroup}
                >
                  <ToggleButton value={true}>
                    {t('baggageYes')}
                  </ToggleButton>
                  <ToggleButton value={false}>
                    {t('baggageNo')}
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>
            </Box>
          </Fade>
        )}

      </DialogContent>

      <DialogActions sx={s.dialogActions}>
        {step === 'input' && (
          <>
            <Button variant="outlined" onClick={handleClose}>
              {t('cancel')}
            </Button>
            <Button variant="contained" onClick={handleCheck}>
              {t('previewCheck')}
            </Button>
          </>
        )}

        {step === 'parsing' && (
          <Button variant="outlined" disabled>
            {t('previewLoading')}
          </Button>
        )}

        {step === 'confirm' && (
          <>
            <Button variant="outlined" onClick={handleBack}>
              {t('backLink')}
            </Button>
            <Button
              variant="contained"
              onClick={handleConfirm}
              disabled={needsBaggage === null}
            >
              {t('confirmButton')}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  )
}
