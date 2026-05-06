# Track the Ticket — Auth migration + Telegram bot

> Feature spec / implementation plan
> Состояние: утверждено к реализации

---

## 1. Что уже есть

### Backend (`services/`)
- **FastAPI** на `services/api/main.py` — endpoints: `/parse`, `/subscriptions` (GET/POST/DELETE), `/subscriptions/{id}/check`, `/health`. Static-mount `/screenshots` отдаёт JPEG'и из `services/screenshots/`.
- **SQLite БД** `data/tracktheticket.db`. Таблицы:
  - `subscriptions` — подписки. Колонка `user_id` сейчас захардкожена в `"default"`. Реальной мульти-юзерности нет.
  - `airlines` — кэш `airline_name → airline_url`.
  - `price_checks` — история проверок (amount, currency, via, screenshot_path, checked_at).
  - `strategies` — записанный action-list для record-and-replay (по подписке).
- **Pipeline проверки цены** (`services/price_checker/price_checker.py`):
  1. `_resolve_job` — резолвит подписку и URL авиакомпании (через кэш или `airline_url_finder`).
  2. Если есть `strategy` → `_try_replay_with_retries` (3 попытки с растущими паузами, каждая в свежем incognito-контексте, верификация через Sonnet).
  3. Иначе `_run_llm_pipeline_and_record` — Stage A (`vision_search_agent`) + Stage B (`vision_pick_flight_agent`) + verifier, сохранение strategy.
  4. После любой успешной ветки — `_save_check_result` пишет JPEG на диск + строку в `price_checks`.
- **Retention скриншотов**: 7 дней, чистится в начале каждого `check_price` (`_prune_old_screenshots`). Строки `price_checks` живут вечно.
- **Verifier** (`services/agents/strategy_verifier.py`) — один Sonnet-вызов: «есть ли рейс с departure_time {time}?» + «какая цена в этой строке?». Возвращает `VerificationResult(verified, price)`.

### Frontend (`frontend/`)
- React 18 + Vite + TypeScript + MUI v5 + Redux Toolkit + axios.
- На `DashboardPage` рендерятся `SubscriptionCard` — маршрут, авиакомпания, дата/время, баггаж, last_checked_at, последняя цена + кликабельный thumbnail скриншота → lightbox.
- **Сейчас стоит aws-amplify v6 (Cognito)** в `package.json` и в `src/components/AuthProvider.tsx`, `AuthGuard.tsx`, `LoginPage.tsx`, `config/amplify.ts`, `hooks/useAuth.ts`, `store/slices/authSlice.ts`. **Это всё уходит.**

### Правила проекта (`CLAUDE.md`)
- Все sx-стили — в файлах `<Component>.styles.ts`. Никаких инлайн-`sx` в JSX.
- User-facing строки — только в `frontend/src/i18n/translations.ts` (ru + en).
- Mobile-first: `xs` первым в responsive sx.
- Комментарии в коде — только на английском.
- Никаких `console.log` в коммитах.

---

## 2. Что меняем — высокоуровневый список

1. **Сносим Cognito.** Полностью убираем `aws-amplify` и связанный код.
2. **Ставим Firebase Authentication.** Социальные провайдеры: Google, Apple, Facebook. Хостинг — Firebase Hosting.
3. **Заводим реальных юзеров.** Таблица `users` с Firebase UID; `subscriptions.user_id` начинает указывать на неё.
4. **Создаём Telegram-бота** (long-polling, отдельный процесс, библиотека `python-telegram-bot`).
5. **Связка веб ↔ бот** через one-time deep-link токен (кнопка + QR-код на одном URL).
6. **Notifier**: после каждой успешной проверки `check_price` бот отправляет пользователю в Telegram скриншот + цену.

### Зафиксированные решения

| Вопрос | Решение |
|---|---|
| Auth-провайдер | Firebase Authentication |
| Соц-логины | Google, Apple, Facebook |
| Multi-user | Да, через Firebase UID; таблица `users` |
| Bot транспорт | Long-polling, отдельный процесс |
| Bot библиотека | `python-telegram-bot` |
| Связь чат↔юзер | 1:1, колонка `users.telegram_chat_id` |
| Когда уведомлять | После **каждой** успешной проверки |
| Канал связки | Deep-link с одноразовым токеном (UUID, TTL 10 мин), кнопка + QR на одном URL |
| Хостинг фронта | Firebase Hosting |
| Содержимое TG-сообщения | `sendPhoto` JPEG + caption (маршрут, дата, цена, время проверки) |

---

## 3. Порядок имплементации (6 этапов)

Этапы строго последовательны: каждый следующий зависит от предыдущего. После каждого этапа должна быть рабочая система — никаких незакоммиченных «полу-фич».

---

### Этап 1 — Backend Firebase Auth + таблица `users`

**Цель:** API распознаёт пользователя по Firebase ID-токену; в БД появляются реальные `user_id`.

#### 1.1. Зависимости
- В `services/requirements.txt` (или где у нас pip-зависимости) добавить `firebase-admin>=6.0`.
- Получить Firebase service-account JSON из консоли Firebase (Project settings → Service accounts → Generate new private key). Положить файл вне репо. Путь — в env `FIREBASE_SERVICE_ACCOUNT_PATH`.

#### 1.2. Инициализация Firebase Admin
Новый файл: **`services/common/firebase_auth.py`**.
- Singleton-инициализация: `firebase_admin.initialize_app(credentials.Certificate(path))` при первом обращении.
- Функция `verify_id_token(token: str) -> dict` — обёртка над `firebase_admin.auth.verify_id_token`. Логирует expired/invalid токены, кидает `HTTPException(401)`.

#### 1.3. FastAPI dependency `current_user`
В том же файле или в `services/api/dependencies.py`:
```python
async def current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer token and return (or lazily create) the User row."""
```
Поведение:
- Парсит `Bearer <token>`.
- Зовёт `verify_id_token` → получает `uid`, `email`.
- Через `upsert_user(db, uid, email)` лениво создаёт строку в `users` если её нет.
- Возвращает SQLAlchemy `User`.

Все защищённые endpoints получают `current_user` через `Depends`.

#### 1.4. Модель `User`
В `services/common/db_models.py`:
```python
class User(Base):
    __tablename__ = "users"
    id               = Column(String, primary_key=True)        # Firebase UID
    email            = Column(String, nullable=True)
    telegram_chat_id = Column(BigInteger, nullable=True, index=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)
```

`subscriptions.user_id` остаётся `String`, но теперь должен ссылаться на `users.id`. Добавить `ForeignKey("users.id")`.

**Существующие данные:** на проде ещё нет реальных юзеров. Удалить файл `data/tracktheticket.db`, при старте API он пересоздастся через `Base.metadata.create_all`. `airlines` тоже потеряются — это кэш, не страшно.

#### 1.5. Queries
В `services/common/queries.py` добавить:
- `get_user(db, user_id) -> Optional[User]`
- `upsert_user(db, user_id, email) -> User`

#### 1.6. Протянуть `current_user` в endpoints
Изменения в `services/api/main.py`:
- `POST /subscriptions` — записывает `sub.user_id = current_user.id`.
- `GET /subscriptions` — фильтрует `WHERE user_id = current_user.id`. Удалить захардкоженный `"default"`.
- `DELETE /subscriptions/{id}` — проверяет `sub.user_id == current_user.id`, иначе 404.
- `POST /subscriptions/{id}/check` — то же самое.
- `/parse` и `/health` — оставить публичными.

#### 1.7. Тест этапа
- Получить вручную ID-токен из Firebase (через тестовый фронтенд или `firebase login` REST hack).
- `curl -H "Authorization: Bearer <token>" /subscriptions` → 200.
- Без токена → 401.
- Создать подписку, удалить — работает.

---

### Этап 2 — Frontend swap на Firebase Auth

**Цель:** пользователь логинится через Google / Apple / Facebook; `apiClient` шлёт Firebase ID-токен.

#### 2.1. Удалить Cognito
Удалить файлы:
- `frontend/src/config/amplify.ts`
- `frontend/src/components/AuthProvider.tsx` (будет переписан)
- `frontend/src/components/AuthGuard.tsx` (будет переписан)
- `frontend/src/hooks/useAuth.ts` (будет переписан)
- `frontend/src/store/slices/authSlice.ts` (будет переписан)
- `frontend/src/pages/LoginPage.tsx`, `LoginPage.styles.ts` (будут переписаны)

В `package.json` — убрать `aws-amplify`. Переустановить.

#### 2.2. Установить Firebase
```bash
npm install firebase qrcode.react
```
`qrcode.react` понадобится в Этапе 5 — поставим заранее.

#### 2.3. Конфиг
Новый файл: **`frontend/src/config/firebase.ts`**:
```ts
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, OAuthProvider, FacebookAuthProvider } from 'firebase/auth'

export const firebaseApp = initializeApp({
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId:             import.meta.env.VITE_FIREBASE_APP_ID,
  // ...
})
export const auth = getAuth(firebaseApp)
export const googleProvider = new GoogleAuthProvider()
export const appleProvider = new OAuthProvider('apple.com')
export const facebookProvider = new FacebookAuthProvider()
```

В `.env.local` (локально) и Firebase Hosting env (проде) — все `VITE_FIREBASE_*` переменные.

#### 2.4. Новый `AuthProvider`
**`frontend/src/components/AuthProvider.tsx`**:
- Подписывается на `onAuthStateChanged(auth, ...)`.
- Кладёт в Redux: `{ uid, email, displayName, photoURL, idToken }` (последний обновляем раз в N минут или просто всегда тянем `getIdToken()` в interceptor'е).
- При `null` юзере — диспатчит `clearAuth()`.

#### 2.5. Новый `LoginPage`
**`frontend/src/pages/LoginPage.tsx`** + **`LoginPage.styles.ts`**:
- Три кнопки: Google / Apple / Facebook. Каждая — отдельный `Button` с иконкой провайдера (можно из `react-icons/fc` для Google, `react-icons/fa` для Apple/Facebook, либо SVG-инлайн).
- Логика клика:
  - Desktop: `signInWithPopup(auth, provider)`.
  - Mobile (детекция через `window.matchMedia('(max-width: 768px)')` или просто всегда `signInWithRedirect` на touch-устройствах): `signInWithRedirect(auth, provider)` + `getRedirectResult` при загрузке.
- На ошибки — Snackbar с переводом.
- Стилистика: берри-палитра + glassmorphism как в существующем `LoginPage`. Все sx — в `.styles.ts`.

#### 2.6. `apiClient` interceptor
В `frontend/src/api/index.ts`:
```ts
apiClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()  // Firebase SDK кэширует и ротирует
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```
Убрать чтение токена из Redux (сейчас `store.getState().auth.token`).

#### 2.7. `AuthGuard`
**`frontend/src/components/AuthGuard.tsx`**:
- Если `auth.currentUser === null` И `loading === false` → редирект на `/login`.
- Если `loading === true` — спиннер.

#### 2.8. Translations
В `frontend/src/i18n/translations.ts` добавить (ru + en):
```
loginWithGoogle:   "Войти через Google" / "Sign in with Google"
loginWithApple:    "Войти через Apple"  / "Sign in with Apple"
loginWithFacebook: "Войти через Facebook" / "Sign in with Facebook"
loginError:        "Ошибка входа. Попробуйте ещё раз." / "Sign-in failed. Try again."
```

#### 2.9. Тест этапа
- Логин через каждого из трёх провайдеров → попадаем на Dashboard.
- В Network видно `Authorization: Bearer eyJ...` на каждом запросе.
- Logout → редирект на login.
- Открытие Dashboard без логина → редирект на login.

---

### Этап 3 — Backend для Telegram-связки

**Цель:** API умеет генерить link-token, бот может его «погасить», фронт может узнать статус.

#### 3.1. Модель `TelegramLinkToken`
В `services/common/db_models.py`:
```python
class TelegramLinkToken(Base):
    __tablename__ = "telegram_link_tokens"
    token      = Column(String, primary_key=True)              # uuid4 hex
    user_id    = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at    = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

TTL: 10 минут (константа `LINK_TOKEN_TTL_MINUTES = 10`).

#### 3.2. Queries
В `services/common/queries.py`:
- `create_link_token(db, user_id) -> str` — генерит uuid4 hex, удаляет предыдущие неиспользованные токены этого юзера (один активный за раз), вставляет новый, возвращает токен-строку.
- `claim_link_token(db, token, chat_id) -> bool` — проверяет: токен есть, `used_at IS NULL`, `expires_at > now`. Если ОК → `users.telegram_chat_id = chat_id`, `token.used_at = now()`, возвращает `True`. Иначе `False`.
- `unlink_telegram(db, user_id) -> None` — обнуляет `telegram_chat_id`.

#### 3.3. Endpoints
В `services/api/main.py`:

**`POST /telegram/link-token`** (защищённый):
- Возвращает `{token: str, expires_at: ISO, bot_username: str, deep_link: str}`.
- `deep_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={token}"`.
- `TELEGRAM_BOT_USERNAME` — из env, читать через `os.environ`.

**`GET /telegram/status`** (защищённый):
- Возвращает `{linked: bool, chat_id_masked: str | None}`.
- `chat_id_masked` — последние 4 цифры (UI-only косметика).

**`DELETE /telegram/unlink`** (защищённый):
- Зовёт `unlink_telegram`. 200 OK.

**`POST /telegram/claim`** (внутренний):
- Body: `{token: str, chat_id: int}`.
- Защита: один из вариантов:
  - (A) Endpoint доступен только с `localhost` (бот и API на одной машине). Проверка `request.client.host == "127.0.0.1"`.
  - (B) Shared secret в env `TELEGRAM_INTERNAL_SECRET`, бот шлёт его в header `X-Internal-Secret`.
  - **Рекомендую (B)** — чтобы не зависеть от deploy-топологии.
- Возвращает `{ok: bool, message: str}` — бот это шлёт в чат пользователю.

#### 3.4. Тест этапа
- `curl -H "Authorization: Bearer <user_token>" -X POST /telegram/link-token` → получаем `{token: ..., deep_link: "https://t.me/..."}`.
- `curl -H "X-Internal-Secret: ..." -X POST /telegram/claim -d '{"token":"...","chat_id":12345}'` → `{ok: true}`.
- `curl -H "Authorization: Bearer <user_token>" /telegram/status` → `{linked: true, chat_id_masked: "***2345"}`.
- Повторный claim того же токена → `{ok: false, message: "already used"}`.

---

### Этап 4 — Telegram-бот (отдельный процесс)

**Цель:** запускается рядом с API, ловит `/start <token>`, регистрирует пользователя.

#### 4.1. Зависимости
В `services/requirements.txt`: `python-telegram-bot[job-queue]>=21.0`.

#### 4.2. Структура
```
services/bot/
  __init__.py
  __main__.py        # entrypoint: python -m bot
  main.py            # build Application, register handlers, run_polling()
  handlers.py        # /start, /unlink, /status command handlers
  config.py          # TELEGRAM_BOT_TOKEN, API_BASE_URL, INTERNAL_SECRET
```

#### 4.3. `config.py`
Читает env:
- `TELEGRAM_BOT_TOKEN` — обязателен.
- `TELEGRAM_BOT_USERNAME` — для логов.
- `API_BASE_URL` — где живёт FastAPI (default `http://localhost:8000`).
- `TELEGRAM_INTERNAL_SECRET` — тот же, что в API.

#### 4.4. `handlers.py`
**`/start <token>`:**
- Если `context.args` пуст → отправить welcome-сообщение со ссылкой на сайт.
- Иначе: `httpx.post(f"{API_BASE_URL}/telegram/claim", json={"token": args[0], "chat_id": update.effective_chat.id}, headers={"X-Internal-Secret": ...})`.
- Ответ API → переслать в чат:
  - `ok=true` → «✅ Подключено! Теперь будем присылать сюда результаты проверок цен.»
  - `ok=false, message=expired` → «⏱ Ссылка истекла. Сгенерируй новую на сайте.»
  - `ok=false, message=already_used` → «Эта ссылка уже использована.»
  - `ok=false, message=not_found` → «Ссылка не найдена.»

**`/unlink`:**
- Просит подтверждение inline-кнопкой → дёргает API `/telegram/unlink` (но эндпоинт защищён Firebase токеном — `unlink` со стороны бота сложнее). Вариант: добавить отдельный internal-endpoint `/telegram/unlink-by-chat-id` со shared secret. На MVP можно просто скзать «отвязка через сайт».

**`/status`:**
- Отвечает «подключено» / «не подключено» по факту получения сообщений.

#### 4.5. `main.py`
```python
from telegram.ext import Application, CommandHandler
from .config import TELEGRAM_BOT_TOKEN
from .handlers import start_handler, unlink_handler, status_handler

def run() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("unlink", unlink_handler))
    app.run_polling()
```

`__main__.py` просто вызывает `run()`.

#### 4.6. Запуск
- Локально: два процесса параллельно — `uvicorn api.main:app --reload` и `python -m bot`.
- Обновить `dev.ps1` чтобы стартовал оба (через `Start-Job` или просто два терминала).
- В проде: systemd-сервис / docker-compose service для бота.

#### 4.7. Тест этапа
- На сайте сгенерить токен.
- Открыть `https://t.me/<BotName>?start=<token>` — Telegram открывает бот, отправляет `/start <token>`.
- Бот отвечает «✅ Подключено».
- В БД: `users.telegram_chat_id` обновился.
- `GET /telegram/status` → `linked: true`.

---

### Этап 5 — Frontend Telegram UI

**Цель:** на сайте есть «Подключить Telegram» с QR + кнопкой; виден статус подключения.

#### 5.1. Компоненты
Новый файл: **`frontend/src/components/TelegramConnectModal.tsx`** + **`TelegramConnectModal.styles.ts`**.

Состояния:
- `idle` — кнопка «Получить ссылку».
- `loading` — спиннер.
- `pending` — есть `token`, `deep_link`, показываем:
  - Кнопку `<a href={deep_link}>Открыть в Telegram</a>` — на мобиле тапает и открывает приложение, на десктопе откроется web/desktop-клиент TG.
  - QR-код через `<QRCodeSVG value={deep_link} />` с подписью «Отсканируй с телефона».
  - Таймер обратного отсчёта до `expires_at`.
  - Поллинг `GET /telegram/status` раз в 3 сек до min(5 мин, истечение токена).
- `linked` — «✅ Подключено: ***2345», кнопка «Отвязать».

#### 5.2. Интеграция в UI
- В `SettingsMenu.tsx` (шестерёнка в шапке) добавить пункт «Telegram» → открывает `TelegramConnectModal`.
- Иконка пункта — `TelegramIcon` из `@mui/icons-material` если есть, иначе `ChatIcon`.

#### 5.3. API-методы
В `frontend/src/api/index.ts`:
```ts
export const requestTelegramLinkToken = async () => {
  const { data } = await apiClient.post<{
    token: string
    deep_link: string
    expires_at: string
  }>('/telegram/link-token')
  return data
}

export const getTelegramStatus = async () => {
  const { data } = await apiClient.get<{
    linked: boolean
    chat_id_masked: string | null
  }>('/telegram/status')
  return data
}

export const unlinkTelegram = async () => {
  await apiClient.delete('/telegram/unlink')
}
```

#### 5.4. Translations
В `frontend/src/i18n/translations.ts` добавить (ru + en):
```
connectTelegram:       "Подключить Telegram" / "Connect Telegram"
telegramConnected:     "Telegram подключён" / "Telegram connected"
telegramUnlink:        "Отвязать" / "Unlink"
telegramOpenApp:       "Открыть в Telegram" / "Open in Telegram"
telegramScanQr:        "Или отсканируй QR-код телефоном" / "Or scan the QR code with your phone"
telegramLinkExpired:   "Ссылка истекла, обнови" / "Link expired, refresh"
telegramExpiresIn:     "Истекает через {n} сек" / "Expires in {n} sec"
```

#### 5.5. Тест этапа
- Залогиниться, открыть настройки → Telegram → «Получить ссылку».
- На десктопе сканируем QR → бот отвечает в TG.
- Через ~3 сек модалка обновляется → «✅ Подключено».
- Кликаем «Отвязать» → статус возвращается на «Не подключено».
- На мобильном — то же самое, но тапаем кнопку вместо QR.

---

### Этап 6 — Notifier: уведомления после каждой проверки

**Цель:** после `_save_check_result` пользователь получает в Telegram сообщение со скриншотом и ценой.

#### 6.1. Модуль
Новые файлы:
```
services/notifier/
  __init__.py
  telegram_notifier.py
```

#### 6.2. `telegram_notifier.py`
Функция:
```python
async def send_check_result(
    user_id: str,
    job: _Job,                    # маршрут, дата, время, авиакомпания
    price: Optional[PriceResult],
    screenshot_path: Path,
) -> None:
```

Поведение:
1. `with SessionLocal() as db:` → `user = get_user(db, user_id)`. Если `user is None` или `user.telegram_chat_id is None` → лог «not linked», `return`.
2. Сформировать caption (см. шаблон ниже).
3. `httpx.AsyncClient.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={"photo": open(path, "rb")}, data={"chat_id": chat_id, "caption": ..., "parse_mode": "HTML"})`.
4. Любые ошибки HTTP / сети — логировать, но **не пробрасывать**: проверка цены уже сохранена в БД, недоставленное уведомление не должно валить pipeline.
5. Telegram API rate-limit (30 msg/sec на бота, 1 msg/sec на чат) — на нашем масштабе (десятки юзеров × 2-3 проверки в день) не упрёмся. Если упрёмся — экспоненциальный бэкофф на 429.

#### 6.3. Шаблон caption
```
✈ <b>{origin} → {destination}</b>
{airline} · {date} · {time} · {baggage}

💵 <b>{price} {currency}</b>
🕐 Проверено: {checked_at}
```
Локализация caption делается на бэке по `users.locale` (которой пока нет — поэтому пока EN/RU зашиваем по умолчанию RU, потом протянем locale из фронта).

Если `price is None`:
```
✈ <b>{origin} → {destination}</b>
{airline} · {date} · {time}

⚠ Цену не удалось считать
🕐 Проверено: {checked_at}
```

#### 6.4. Подключение
В `services/price_checker/price_checker.py` в `_save_check_result` после успешной записи в БД:
```python
from notifier.telegram_notifier import send_check_result

async def _save_check_result(page, job, via, price):
    screenshot_path = await _save_final_screenshot(page, job, via)
    # ... save to price_checks ...

    try:
        await send_check_result(
            user_id=job.user_id,        # добавить в _Job!
            job=job,
            price=price,
            screenshot_path=screenshot_path,
        )
    except Exception as exc:
        logger.error(f"[price_checker] notify failed: {exc}", exc_info=True)
```

⚠ Это требует добавить `user_id` в `_Job` и передавать его из `_resolve_job`.

#### 6.5. Тест этапа
- Подключённый юзер запускает проверку (кнопкой `Sync` на карточке).
- Проверка проходит до конца → в Telegram приходит сообщение со скриншотом и ценой.
- Если юзер не подключил Telegram → проверка проходит как обычно, в логах `[notifier] user X not linked, skip`.

---

## 4. Env vars (полный список)

### Backend (`services/.env` или системные)
```
ANTHROPIC_API_KEY=sk-ant-...                 # уже есть
DATABASE_PATH=...                             # опционально
SCREENSHOTS_DIR=...                           # опционально
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
TELEGRAM_BOT_TOKEN=123456:AA...
TELEGRAM_BOT_USERNAME=TrackTheTicketBot       # без @
TELEGRAM_INTERNAL_SECRET=<long random string>
API_BASE_URL=http://localhost:8000            # для бота
```

### Frontend (`frontend/.env.local`)
```
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...         # если используем
VITE_TELEGRAM_BOT_USERNAME=TrackTheTicketBot
```

---

## 5. Что НЕ делаем сейчас (явно отложено)

- **Webhook для бота** — стартуем с long-polling. Перевод на webhook после деплоя на хостинг с публичным HTTPS.
- **Локализация caption в Telegram** — сейчас один язык (RU). Когда заведём `users.locale` на фронте — добавим.
- **Threshold-уведомления** («только если цена изменилась на X%»). Сейчас уведомляем после каждой успешной проверки.
- **Группы / несколько чатов на юзера** — 1:1 only.
- **Email-уведомления как фолбэк** — пока нет.
- **Webhook от Firebase для удалённых аккаунтов** — если юзер удалит Firebase-аккаунт, у нас останутся orphan-записи. Пофиксим отдельной задачей.
- **Миграции БД** (Alembic) — пока пересоздаём БД с нуля. Когда появятся реальные данные — добавим Alembic.

---

## 6. Чеклист готовности фичи

- [ ] Этап 1: Backend Firebase Auth, таблица `users`, защищённые endpoints.
- [ ] Этап 2: Frontend на Firebase, login через Google/Apple/Facebook работает.
- [ ] Этап 3: Endpoints `/telegram/link-token`, `/telegram/status`, `/telegram/claim`, `/telegram/unlink`.
- [ ] Этап 4: Бот стартует, ловит `/start <token>`, привязывает чат.
- [ ] Этап 5: Модалка на сайте с QR + кнопкой + статусом.
- [ ] Этап 6: После каждой успешной проверки приходит сообщение в Telegram.
- [ ] End-to-end: новый юзер регистрируется → создаёт подписку → подключает TG → проверяет цену → получает уведомление.
- [ ] Все строки в `translations.ts` (ru + en).
- [ ] Все sx-стили в `.styles.ts`.
- [ ] Никаких `console.log` в коммитах.
- [ ] Cognito и `aws-amplify` отсутствуют в коде и `package.json`.
