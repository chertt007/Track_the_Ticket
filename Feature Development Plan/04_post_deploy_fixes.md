# Post-Deploy Fixes

> Задачи после первого успешного деплоя на прод.
> Приоритет: сначала починить price check, потом URL.

---

## Задачи

1. ✅ [Починить price check на проде](#1-починить-price-check-на-проде)
2. ⬜ [Красивый URL без `app.`](#2-красивый-url-без-app)
3. ⬜ [Заглушка в `/check` эндпоинте](#3-заглушка-в-check-эндпоинте)

---

## 1. Починить price check на проде

### Симптом
Ответ сервера возвращает `price: null`. Ручной sync через UI не работает.
Автоматические проверки по расписанию (07:00 и 16:00 Asia/Jerusalem) —
под вопросом, скорее всего тоже не работают.

### Диагностика (с чего начать)

**Шаг 1 — посмотреть логи API в момент проверки:**
```bash
ssh deploy@204.168.165.83
cd ~/track-the-ticket
docker compose -f docker-compose.prod.yml logs --tail=100 api
```
Искать строки с `ERROR`, `price_checker`, `playwright`, `check_price`.

**Шаг 2 — проверить Playwright внутри контейнера:**
```bash
docker compose -f docker-compose.prod.yml exec api python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto('https://www.aviasales.ru')
    print('OK:', page.title())
    b.close()
"
```
Если падает — проблема в Playwright/Chromium внутри контейнера.

**Шаг 3 — проверить переменные окружения:**
```bash
docker compose -f docker-compose.prod.yml exec api env | grep -E "ANTHROPIC|FIREBASE|DATABASE|SCREENSHOTS"
```
Убедиться что все переменные подтянулись из `.env`.

**Шаг 4 — проверить доступ к БД:**
```bash
docker compose -f docker-compose.prod.yml exec api python -c "
from common.database import SessionLocal
from common.db_models import Subscription
with SessionLocal() as db:
    subs = db.query(Subscription).all()
    print(f'Subscriptions: {len(subs)}')
    for s in subs:
        print(f'  id={s.id} active={s.is_active} url={s.url[:50]}')
"
```

### Диагностика проведена (2026-05-19)

**Root cause: на VPS нет display server.**

Цепочка:
1. `check_price()` → `_resolve_job()` → авиакомпания "Red Wings" не в кэше `airlines`
2. Запускается `airline_url_finder` — `browser_use` + Chromium с `HEADLESS=False`
3. Chromium стартует, но сразу падает — нет X11/дисплея на VPS
4. CDP-порт не поднимается → `ConnectionRefusedError` → таймаут 30s
5. `find_airline_url_online()` возвращает `None` → `_resolve_job()` возвращает `None` → пропуск

Та же проблема ждёт и основной `price_checker.py` (Playwright, `HEADLESS=False`), как только URL будет найден.

**OPENROUTER_API_KEY** — добавлен в `.env` на сервере и в `.env.prod.example`. Сам по себе не достаточен без дисплея.

### Решение: добавить Xvfb в Docker-образ

Xvfb — виртуальный X-сервер, запускается внутри контейнера, даёт Chromium дисплей для рендеринга. Локальная разработка не меняется (`HEADLESS=False` везде).

**Изменения в `services/Dockerfile`:**
```dockerfile
# Virtual display for headed Chromium (HEADLESS=False)
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*
```

**Изменения в `services/run.py` (или entrypoint):**
Запускать Xvfb перед стартом приложения и выставлять `DISPLAY=:99`:
```bash
Xvfb :99 -screen 0 1280x800x24 &
export DISPLAY=:99
```

Либо через обёртку-скрипт `entrypoint.sh`:
```bash
#!/bin/bash
Xvfb :99 -screen 0 1280x800x24 &
export DISPLAY=:99
exec python run.py
```

После этого оба headed-браузера (`browser_use` в `airline_url_finder` и Playwright в `price_checker`) получат дисплей и смогут запустить Chromium.

---

## 3. Заглушка в `/check` эндпоинте

### Симптом
`POST /subscriptions/{id}/check` всегда возвращает `{"price": null, "currency": "RUB", ...}` — захардкоженная заглушка, не связанная с реальным результатом проверки.

### Решение
После `await check_price(sub_id)` — запросить последнюю строку из `price_checks` для этого `sub_id` и вернуть реальные `amount`, `currency`, `checked_at`.

> ⚠️ Делать после того, как price check полностью заработает (задача 1).

---

## 2. Красивый URL без `app.`

### Цель
Пользователи заходят на `https://track-the-ticket.com` (без `app.`).
`app.track-the-ticket.com` продолжает работать (или редиректит).

### Шаги

**Шаг 1 — Cloudflare DNS:**
Добавить A-запись:
- Name: `@` (корневой домен)
- IPv4: `204.168.165.83`
- Proxy status: DNS only (серое облако)

**Шаг 2 — Caddyfile:**
```
track-the-ticket.com {
    reverse_proxy frontend:80
}

app.track-the-ticket.com {
    redir https://track-the-ticket.com{uri} permanent
}

api.track-the-ticket.com {
    reverse_proxy api:8000
    request_body {
        max_size 10MB
    }
}
```
Скопировать на VPS:
```powershell
scp Caddyfile deploy@204.168.165.83:~/track-the-ticket/
```
Перезапустить Caddy:
```bash
docker compose -f docker-compose.prod.yml restart caddy
```

**Шаг 3 — Firebase Console:**
Authentication → Settings → Authorized domains → Add domain:
- `track-the-ticket.com`

**Шаг 4 — GitHub Secret `VITE_API_URL`:**
Значение остаётся `https://api.track-the-ticket.com` — менять не нужно.

**Шаг 5 — Firebase Authorized domains:**
Уже добавлен `app.track-the-ticket.com`. Добавить `track-the-ticket.com`.

### Проверка
- `https://track-the-ticket.com` → открывается фронт
- `https://app.track-the-ticket.com` → редирект на `track-the-ticket.com`
- Google login работает на новом домене
