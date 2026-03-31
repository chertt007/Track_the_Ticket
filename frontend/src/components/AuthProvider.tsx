import { useAuth } from '../hooks/useAuth'
import { useClickSound } from '../hooks/useClickSound'

interface Props {
  children: React.ReactNode
}

// Thin wrapper that initialises the Amplify Hub listener,
// restores the session on app startup, and sets up global click sounds.
export default function AuthProvider({ children }: Props) {
  useAuth()
  useClickSound()
  return <>{children}</>
}
