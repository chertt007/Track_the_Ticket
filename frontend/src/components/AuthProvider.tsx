import { useAuth } from '../hooks/useAuth'

interface Props {
  children: React.ReactNode
}

// Thin wrapper that initialises the Amplify Hub listener and
// restores the session on app startup. No visual output.
export default function AuthProvider({ children }: Props) {
  useAuth()
  return <>{children}</>
}
