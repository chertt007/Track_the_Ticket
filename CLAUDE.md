# Track the Ticket — Project Rules for Claude

## Project Overview
Flight price tracking app. Users paste Aviasales links, the system monitors prices
and sends Telegram notifications with screenshots.


## Code Style Rules

### Language
- **All comments must be in English.** No Russian comments anywhere in the codebase.
- User-facing strings go into `src/i18n/translations.ts` only (ru + en).

### Styling (MUI sx props)
- **Never inline `sx` objects directly in JSX.**
- Every component has a sibling `ComponentName.styles.ts` file.
- All `sx` objects are defined and exported from the `.styles.ts` file.
- Dynamic styles (depending on props) are exported as functions returning `SxProps<Theme>`.
- Import styles with an alias: `import { fooStyles as s } from './Foo.styles'`

Example structure:
```
src/components/
  SubscriptionCard.tsx          ← component, imports from .styles.ts
  SubscriptionCard.styles.ts    ← all sx objects exported here
```

### Redux
- Each feature has its own slice in `src/store/slices/`.
- Use typed hooks `useAppDispatch` / `useAppSelector` from `src/hooks/index.ts`.

### i18n
- Use `useT()` hook from `src/hooks/useT.ts`.
- All new user-facing strings must be added to both `ru` and `en` in `translations.ts`.

### File naming
- Components: `PascalCase.tsx`
- Styles: `PascalCase.styles.ts`
- Hooks: `camelCase.ts`
- Slices: `camelCaseSlice.ts`

### General
- Mobile-first: always define `xs` breakpoint first in responsive `sx` objects.
- No `console.log` in committed code.
- All new components get a `.styles.ts` sibling from the start.

---

## Tech Stack

### Frontend (`/frontend`)
- React 18 + Vite + TypeScript
- Material UI v5 (MUI)
- Redux Toolkit + RTK Query
- React Router v6
- axios
- aws-amplify v6 (Cognito auth)
- recharts (price charts)
