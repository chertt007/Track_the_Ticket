import { useEffect } from 'react'
import { fetchAuthSession } from 'aws-amplify/auth'
import { Hub } from 'aws-amplify/utils'
import { useAppDispatch } from './index'
import { setAuth, clearAuth, setAuthLoading } from '../store/slices/authSlice'

// Attempt to restore auth state from an existing Amplify session.
// User info is read directly from the ID token payload — no extra API call needed.
// fetchUserAttributes() requires the aws.cognito.signin.user.admin scope which
// we intentionally exclude from the App Client for security.
async function resolveSession(dispatch: ReturnType<typeof useAppDispatch>) {
  try {
    const session = await fetchAuthSession()
    const token = session.tokens?.idToken?.toString() ?? null
    const payload = session.tokens?.idToken?.payload

    if (token && payload) {
      dispatch(setAuth({
        user: {
          sub: (payload['sub'] as string) ?? '',
          email: (payload['email'] as string) ?? '',
          picture: payload['picture'] as string | undefined,
        },
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

    // If the URL contains ?code= we are on the OAuth callback — Amplify is
    // exchanging the code for tokens asynchronously. Skip the immediate
    // resolveSession call and wait for the Hub 'signedIn' event instead.
    // Otherwise resolve the session right away (normal page load / refresh).
    const isOAuthCallback = new URLSearchParams(window.location.search).has('code')
    if (!isOAuthCallback) {
      resolveSession(dispatch)
    }

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
