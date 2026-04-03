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

### AI Agent (`/services/strategy-agent`)
- OpenAI Agents SDK (`openai-agents`) + LiteLLM + OpenRouter
- Default model: `google/gemini-2.0-flash`
- 4-file pattern: `lambda_handler.py`, `agent.py`, `templates.py`, `observability.py`
- LangFuse for LLM call tracing

### Infrastructure
- AWS: Lambda Docker, API Gateway HTTP v2, Cognito, RDS PostgreSQL, S3, SQS, EventBridge
- Terraform (prod only), S3 + DynamoDB remote state
- GitHub Actions CI/CD

---

## Core Pipeline (order matters)

1. **link-parser** — user pastes URL → Playwright intercepts tickets-api → returns structured
   flight data `{ origin_iata, destination_iata, departure_date, flight_number, price, ... }`
2. **strategy-agent** — receives parsed flight data → builds `strategy_json` (how to monitor prices)
3. **First price check** — strategy is executed once to verify it works
4. **Subscription created** — ONLY after a successful first price check. No subscription row is
   written to the DB before this point. Parsing alone does NOT create a subscription.
5. **Periodic price-checker** — runs on schedule, uses strategy to check prices → Telegram notification on change.

---

## DB Schema
- `users`: id, cognito_id, email, telegram_id
- `search_strategies`: id, airline_name, airline_domain, strategy_json (JSONB), success_rate
- `subscriptions`: id, user_id, strategy_id, flight_number, airline, origin_iata,
  destination_iata, departure_date, departure_time, baggage_info, source_url,
  is_active, check_frequency (DEFAULT 3), last_checked_at, last_notified_at
- `price_history`: id, subscription_id, price, currency, s3_key, checked_at, status

---

## Development Approach
- **Frontend First**: UI with mock data before backend infrastructure.
- Modules are developed sequentially — see Notion plan for 11-module breakdown.
- Git commits from Windows terminal only (not from Claude's Linux sandbox).
- Commit message format: `FE-04: short description`
