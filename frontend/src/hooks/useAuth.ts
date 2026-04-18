// Auth is disabled for the local-only phase — no Cognito, no network calls.
// When real auth is introduced (simple JWT against our own API), restore the
// session-resolution logic here. The authSlice is kept intact for that future.
export function useAuth() {
  // intentionally a no-op
}
