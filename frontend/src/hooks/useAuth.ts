import { useEffect } from 'react'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '../config/firebase'
import { useAppDispatch } from '.'
import { clearAuth, setUser } from '../store/slices/authSlice'

/**
 * Subscribe to Firebase auth state changes and mirror them into Redux.
 *
 * Mounted exactly once at the app root (via AuthProvider). On startup it
 * fires with the persisted user (or null), so Redux's `loading` flag
 * flips to `false` as soon as Firebase resolves the session.
 */
export function useAuth() {
  const dispatch = useAppDispatch()

  useEffect(() => {
    return onAuthStateChanged(auth, (user) => {
      if (user) {
        dispatch(setUser({
          uid:         user.uid,
          email:       user.email,
          displayName: user.displayName,
          photoURL:    user.photoURL,
        }))
      } else {
        dispatch(clearAuth())
      }
    })
  }, [dispatch])
}
