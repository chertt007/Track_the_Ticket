import Box from '@mui/material/Box'
import WbSunnyIcon from '@mui/icons-material/WbSunny'
import CloudIcon from '@mui/icons-material/Cloud'
import FlightIcon from '@mui/icons-material/Flight'
import { skyWidgetStyles as s } from './HeaderSkyWidget.styles'

export default function HeaderSkyWidget() {
  return (
    <Box sx={s.container}>
      <Box sx={s.sun}>
        <WbSunnyIcon sx={s.sunIcon} />
      </Box>
      <Box sx={s.cloud}>
        <CloudIcon sx={s.cloudIcon} />
      </Box>
      <Box sx={s.plane}>
        <FlightIcon sx={s.planeIcon} />
      </Box>
    </Box>
  )
}
