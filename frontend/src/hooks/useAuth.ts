import { useEffect } from 'react'
import { fetchAuthSession, getCurrentUser } from 'aws-amplify/auth'
import { Hub } from 'aws-amplify/utils'
import { useAppDispatch } from './index'
import { setAuth, clearAuth, setAuthLoading } from '../store/slices/authSlice'

// Attempt to restore auth state from an existing Amplify session.
// Called once on app mount via AuthProvider.
async function resolveSession(dispatch: ReturnType<typeof useAppDispatch>) {
  try {
    const [session, user] = await Promise.all([fetchAuthSession(), getCurrentUser()])
    const token = session.tokens?.idToken?.toString() ?? null
    if (token) {
      dispatch(setAuth({
        user: { sub: user.userId, email: user.signInDetails?.loginId ?? '' },
        token,
      }))
    } else {
      dispatch(clearAuth())
    }
  } catch {
    // No active session — user is not authenticated
    dispatch(clearAuth())
  }
}

// useAuth sets up the Amplify Hub listener and resolves the session on first mount.
// Should be called once in AuthProvider, not in individual components.
export function useAuth() {
  const dispatch = useAppDispatch()

  useEffect(() => {
    dispatch(setAuthLoading(true))
    resolveSession(dispatch)

    // Listen for Cognito auth events (signIn, signOut, tokenRefresh)
    const unsubscribe = Hub.listen('auth', ({ payload }) => {
      switch (payload.event) {
        case 'signedIn':
          resolveSession(dispatch)
          break
        case 'signedOut':
          dispatch(clearAuth())
          break
        case 'tokenRefresh':
          resolveSession(dispatch)
          break
        default:
          break
      }
    })

    return () => unsubscribe()
  }, [dispatch])
}
