# Track the Ticket — Deployment Checklist

> Живой список всего, что нужно перенести/настроить при деплое на реальный сервер.
> Обновляется по ходу реализации фич. Каждый раз, когда мы добавляем новую env var,
> новый секрет, новый внешний сервис или новый процесс — эта запись попадает сюда.

---

## 1. Секрет-файлы (НЕ в репо)

| Что | Где сейчас (локально) | Куда на сервер | Источник |
|---|---|---|---|
| Firebase Admin SDK service-account JSON | `C:\Git\Secrets\track-the-ticket-firebase-adminsdk-fbsvc-2a94664c18.json` | `/etc/track-the-ticket/firebase-sa.json` (или другой защищённый путь, mode 600, владелец сервиса) | Firebase Console → Project settings → Service accounts → Generate new private key |

**Правила:**
- Никогда не коммитим эти файлы.
- На сервере ставим `chmod 600` и владельцем — пользователя, под которым работает API.
- При смене ключа (компрометация / ротация) — заменяем файл, рестартуем API.

---

## 2. Backend env vars (`services/`)

| Переменная | Обязательная | Пример | Назначение |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | да | `sk-ant-...` | Anthropic API для verifier и vision-агентов |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | да | `/etc/track-the-ticket/firebase-sa.json` | Путь к service-account JSON для верификации ID-токенов |
| `DATABASE_PATH` | нет | `/var/lib/track-the-ticket/tracktheticket.db` | Полный путь к SQLite-файлу. По умолчанию — `<repo>/data/tracktheticket.db` |
| `SCREENSHOTS_DIR` | нет | `/var/lib/track-the-ticket/screenshots` | Где хранятся JPEG'и проверок. По умолчанию — `services/screenshots/` |

**Будут добавлены позднее (Этапы 3-4):**
- `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather.
- `TELEGRAM_BOT_USERNAME` — без `@`, для генерации deep-link.
- `TELEGRAM_INTERNAL_SECRET` — длинная случайная строка, shared secret между API и ботом для `/telegram/claim`.
- `API_BASE_URL` — где живёт FastAPI (нужен боту, default `http://localhost:8000`).

---

## 3. Frontend env vars (`frontend/.env.local` / Firebase Hosting env)

> Будут заведены на Этапе 2. Записываю заранее, чтобы не забыть.

| Переменная | Назначение |
|---|---|
| `VITE_API_URL` | URL бэкенда (прод: `https://api.<домен>`) |
| `VITE_FIREBASE_API_KEY` | Из Firebase Console → Project settings → Web app config |
| `VITE_FIREBASE_AUTH_DOMAIN` | То же |
| `VITE_FIREBASE_PROJECT_ID` | То же |
| `VITE_FIREBASE_APP_ID` | То же |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | То же (если используем) |
| `VITE_TELEGRAM_BOT_USERNAME` | Без `@`, для отображения в UI |

`VITE_*` переменные **встраиваются в бандл при билде**, так что на сервере они должны быть выставлены до запуска `npm run build`.

---

## 4. Внешние сервисы — что нужно настроить вручную

### Firebase Console
- [ ] Создан проект (✅ уже сделано — `track-the-ticket`).
- [ ] Service-account JSON сгенерирован и положен на сервер (см. раздел 1).
- [ ] Authentication → Sign-in method → включены провайдеры: **Google**, **Apple**, **Facebook**.
  - Apple: нужны Apple Developer credentials (Services ID, Key ID, Team ID, Private Key).
  - Facebook: нужны App ID + App Secret из Facebook for Developers.
- [ ] Authentication → Settings → Authorized domains: добавить прод-домен фронта.
- [ ] (Опционально) Firebase Hosting подключён к домену.

### Telegram (Этап 4)
- [ ] Бот создан через @BotFather, получен `TELEGRAM_BOT_TOKEN`.
- [ ] У бота включён privacy mode по умолчанию (нам команд `/start` хватает).
- [ ] Username бота записан в `TELEGRAM_BOT_USERNAME` (и `VITE_TELEGRAM_BOT_USERNAME` на фронте).

---

## 5. БД и данные

- При первом деплое БД создаётся автоматически через `Base.metadata.create_all` на старте API.
- **Сейчас миграций нет** — изменения схемы требуют ручного `DROP DATABASE` или Alembic (поставим, когда появятся реальные данные, см. раздел "что НЕ делаем сейчас" в плане).
- Каталог `data/` и `services/screenshots/` (или их аналоги через env) должны быть writable пользователем, под которым крутится API.
- Скриншоты живут 7 дней (политика retention в `_prune_old_screenshots`); строки `price_checks` — вечно.

---

## 6. Процессы на сервере

### Сейчас (Этап 1)
- **API** — `uvicorn api.main:app` (один процесс).

### После Этапа 4
- **Bot** — `python -m bot` (отдельный процесс, long-polling). Работает на той же машине, или на отдельной с `API_BASE_URL` указывающим на API.

Рекомендуется: systemd-юниты (`track-the-ticket-api.service`, `track-the-ticket-bot.service`) или Docker Compose с двумя сервисами.

---

## 7. Что НЕ делаем при первом деплое (явно отложено)

- Webhook для Telegram-бота — стартуем с long-polling, переедем когда будет публичный HTTPS.
- Alembic-миграции — пока пересоздаём БД с нуля.
- Email-фолбэк уведомлений.
- Webhook от Firebase для удалённых аккаунтов (orphan-записи в `users`).
- Prod-обсервабилити (Sentry / Langfuse в проде) — есть локальная конфигурация Langfuse, но prod-ключи не выставлены.

---

## 8. Чеклист первого деплоя

- [ ] Сервер с Python 3.12+, Node 20+, доступ в интернет, открыт нужный порт.
- [ ] Клонирован репо, установлены зависимости (`pip install -r services/requirements.txt`, `npm ci` в `frontend/`).
- [ ] `playwright install chromium` (нужен для price_checker).
- [ ] Все секреты из раздела 1 положены на сервер.
- [ ] Все env vars из раздела 2 выставлены (через systemd `Environment=` или `.env`).
- [ ] Firebase Console: всё из раздела 4 настроено.
- [ ] `npm run build` фронта (с `VITE_*` env'ами выставленными).
- [ ] Билд фронта задеплоен (Firebase Hosting / nginx static).
- [ ] API стартует, отвечает 200 на `/health`.
- [ ] (После Этапа 4) Бот стартует, лог показывает успешное long-polling.
- [ ] End-to-end: логин с прод-фронта → создание подписки → проверка цены → (Этап 6) уведомление в Telegram.
