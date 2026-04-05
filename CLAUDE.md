# Track the Ticket — Project Rules for Claude

## Project Overview
Flight price tracking app. Users paste Aviasales links, the system monitors prices
and sends Telegram notifications with screenshots.

**Notion project page:** https://www.notion.so/330822365727812a9157f592ad9a51fc

---

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

### Backend (`/services/api`)
- FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2
- Deployed as Lambda Docker via Mangum

### Price-Checker Agent (`/services/price-checker`)
- browser-use + langchain-openai + OpenRouter
- Default model: `google/gemini-2.5-flash`
- 3-file pattern: `lambda_handler.py`, `agent.py`, `requirements.txt`
- Agent navigates airline website via vision, finds price, takes screenshot

### Infrastructure
- AWS: Lambda Docker, API Gateway HTTP v2, Cognito, RDS PostgreSQL, S3, SQS, EventBridge
- Terraform (prod only), S3 + DynamoDB remote state
- GitHub Actions CI/CD

---

## Core Pipeline (order matters)

1. User pastes Aviasales link → frontend calls `POST /parse` → gets structured flight data
2. Frontend shows flight card + asks about baggage preference
3. User confirms → `POST /subscriptions` with all flight data → subscription created immediately
   with status `active`, expires_at = now + 14 days
4. **price-checker Lambda** — EventBridge cron 08:00 / 16:00 / 21:00 Israel time (UTC+3) →
   fetches all active subscriptions → iterates sequentially → for each runs browser-use agent
   on the airline website → finds current price → takes screenshot
5. Screenshot → S3 (`s3_key`), price + s3_key → `price_history`
6. Always (every check, not only on change) → Telegram notification to user + data visible on frontend
7. After 14 days → subscription auto-deactivated

### Removed from pipeline
- ~~strategy-agent~~ — removed entirely, no strategy_json needed
- ~~link-parser Lambda~~ — removed, parsing is synchronous via `POST /parse`
- ~~First price check before subscription~~ — subscription created immediately after user confirms

### Price-checker service
- Location: `/services/price-checker/`
- Tech: browser-use + langchain-openai + OpenRouter (`google/gemini-2.5-flash`)
- Entry: `lambda_handler.py` — processes all active subscriptions sequentially
- Uses airline website URL derived from subscription's `airline_domain` field

---

## DB Schema
- `users`: id, cognito_id, email, telegram_id
- `subscriptions`: id, user_id, flight_number, airline, airline_domain, origin_iata,
  destination_iata, departure_date, departure_time, baggage_info, source_url,
  status, is_active, expires_at, check_frequency (DEFAULT 3), last_checked_at, last_notified_at
- `price_history`: id, subscription_id, price, currency, s3_key, checked_at, status

Note: `search_strategies` table is no longer used. `strategy_id` on subscriptions is nullable.

---

## Development Approach
- **Frontend First**: UI with mock data before backend infrastructure.
- Modules are developed sequentially — see Notion plan for 11-module breakdown.
- Git commits from Windows terminal only (not from Claude's Linux sandbox).
- Commit message format: `FE-04: short description`
