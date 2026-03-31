import type { SxProps, Theme } from '@mui/material'
import { berryPalette } from '../theme'

export const authGuardStyles = {
  spinnerBox: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
  } as SxProps<Theme>,

  spinner: {
    color: berryPalette.raspberry,
  } as SxProps<Theme>,
}
