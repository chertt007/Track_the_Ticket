# Post-Deploy Fixes

> Задачи после первого успешного деплоя на прод.
> Приоритет: сначала починить price check, потом URL.

---

## Задачи

1. ⬜ [Починить price check на проде](#1-починить-price-check-на-проде)
2. ⬜ [Красивый URL без `app.`](#2-красивый-url-без-app)

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

### Вероятные причины
- Playwright не может запустить Chromium в Docker (нет `--no-sandbox` или системных зависимостей)
- `SCREENSHOTS_DIR` не существует внутри контейнера (`/data/screenshots/`)
- Aviasales изменил структуру страницы — парсер возвращает `None`
- `ANTHROPIC_API_KEY` не подтянулся → vision-агент падает → цена `null`

### После диагностики
Зафиксировать root cause и написать fix здесь.

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
