import { Amplify } from 'aws-amplify'

// Cognito values come from environment variables set per environment.
// During local development without real Cognito, set VITE_COGNITO_* in .env.local.
// Placeholder values prevent runtime crash — signInWithRedirect will fail gracefully.
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId:
        import.meta.env.VITE_COGNITO_USER_POOL_ID ?? 'us-east-1_PLACEHOLDER',
      userPoolClientId:
        import.meta.env.VITE_COGNITO_CLIENT_ID ?? 'PLACEHOLDER_CLIENT_ID',
      loginWith: {
        oauth: {
          domain:
            import.meta.env.VITE_COGNITO_DOMAIN ??
            'placeholder.auth.us-east-1.amazoncognito.com',
          scopes: ['email', 'openid', 'profile'],
          redirectSignIn: [window.location.origin + '/dashboard'],
          redirectSignOut: [window.location.origin + '/login'],
          responseType: 'code' as const,
        },
      },
    },
  },
})
