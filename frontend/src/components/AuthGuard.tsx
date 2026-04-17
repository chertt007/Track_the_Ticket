interface Props {
  children: React.ReactNode
}

// TODO: auth temporarily bypassed — Cognito removed, new auth TBD.
export default function AuthGuard({ children }: Props) {
  return <>{children}</>
}
