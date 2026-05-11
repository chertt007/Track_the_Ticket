# Деплой на Hetzner VPS

> **Цель этого документа:** конкретный пошаговый план переноса
> Track the Ticket из локального dev-окружения на VPS Hetzner Cloud.
> Общий чеклист переменных/секретов смотри в
> [deployment_checklist.md](deployment_checklist.md) — этот файл его
> *дополняет* провайдер-специфичными шагами.

---

## 1. Выбор машины

Сейчас в проекте один пользователь, до ~5 подписок. Шедулер крутит
проверки **последовательно** (см. [02_concurrent_price_checks.md](02_concurrent_price_checks.md)).

| Конфиг | RAM | vCPU | Цена/мес | Когда подходит |
|---|---|---|---|---|
| **CX22** | 4 ГБ | 2 | ~€4 | ✅ Стартовая. 1 пользователь, до 10 подписок, sequential checks |
| CX32 | 8 ГБ | 4 | ~€8 | Когда включим параллельные проверки (3-5) |
| CX42 | 16 ГБ | 8 | ~€16 | 10+ юзеров, параллель 5+, готовность к Postgres |

**Локация:** Falkenstein (DE) или Helsinki (FI) — обе ОК. Helsinki чуть
ближе к израильским юзерам по латентности, но разница ~30 мс — не
критично для нашего юзкейса (фоновые проверки + редкие HTTP-запросы).

**ОС:** Ubuntu 24.04 LTS — стандарт, есть в шаблонах Hetzner, поддержка
до 2029.

---

## 2. Подготовка VPS (one-time)

```bash
# Создаётся через Hetzner Cloud Console или CLI (hcloud)
# Например:
#   hcloud server create --name ttt-prod --type cx22 --image ubuntu-24.04 \
#                        --location fsn1 --ssh-key <your-key-id>

# Подключаемся:
ssh root@<vps-ip>

# Создаём непривилегированного пользователя для приложения
adduser --disabled-password --gecos "" ttt
usermod -aG sudo ttt   # временно, для setup; потом убрать

# Обновление + базовые пакеты
apt update && apt upgrade -y
apt install -y python3.12 python3.12-venv python3-pip git curl ufw nginx certbot python3-certbot-nginx

# Node 20 (для билда фронта; на VPS можно билдить прямо тут или билдить локально и заливать dist/)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Playwright нужны системные зависимости Chromium — поставим после pip install
```

---

## 3. Файрвол

```bash
ufw allow OpenSSH
ufw allow 80/tcp     # HTTP (для редиректа на HTTPS и certbot)
ufw allow 443/tcp    # HTTPS
ufw enable
```

Порт 8000 (API) и 5173 (Vite dev) **наружу не открываем** — API
проксируется через nginx, фронт билдится в статику.

---

## 4. Развёртывание кода

```bash
# Под пользователем ttt
su - ttt
git clone https://github.com/<your>/Track_the_Ticket.git /home/ttt/app
cd /home/ttt/app

# Backend venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r services/requirements.txt
playwright install chromium
# Playwright допросит установить системные deps:
playwright install-deps chromium    # требует sudo, под root заранее

# Frontend
cd frontend
npm ci
# .env.production создаём ниже, перед npm run build
```

---

## 5. Каталоги для данных

```bash
sudo mkdir -p /var/lib/track-the-ticket/{data,screenshots}
sudo chown -R ttt:ttt /var/lib/track-the-ticket
sudo chmod 750 /var/lib/track-the-ticket
```

Они переопределяются env-переменными `DATABASE_PATH` и `SCREENSHOTS_DIR`
(см. [deployment_checklist.md](deployment_checklist.md) §2).

---

## 6. Секреты

```bash
sudo mkdir -p /etc/track-the-ticket
sudo chmod 750 /etc/track-the-ticket
# Заливаем (scp/rsync с локалки):
#   - firebase-sa.json  (mode 600, owner ttt)
sudo chown ttt:ttt /etc/track-the-ticket/firebase-sa.json
sudo chmod 600 /etc/track-the-ticket/firebase-sa.json
```

---

## 7. Environment файл

`/etc/track-the-ticket/env` (mode 640, owner root:ttt):

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/track-the-ticket/firebase-sa.json

# Paths
DATABASE_PATH=/var/lib/track-the-ticket/data/tracktheticket.db
SCREENSHOTS_DIR=/var/lib/track-the-ticket/screenshots

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=track_the_ticket_bot
TELEGRAM_INTERNAL_SECRET=<openssl rand -hex 32>
API_BASE_URL=http://127.0.0.1:8000

# Scheduler (опционально, дефолты 7 и 17 OK)
# SCHEDULE_MORNING_HOUR=7
# SCHEDULE_AFTERNOON_HOUR=17

# Logging / observability (опционально)
# LANGFUSE_PUBLIC_KEY=...
# LANGFUSE_SECRET_KEY=...
```

---

## 8. systemd units

### `/etc/systemd/system/ttt-api.service`

```ini
[Unit]
Description=Track the Ticket API
After=network.target

[Service]
Type=simple
User=ttt
Group=ttt
WorkingDirectory=/home/ttt/app/services
EnvironmentFile=/etc/track-the-ticket/env
ExecStart=/home/ttt/app/.venv/bin/python run.py
Restart=on-failure
RestartSec=5s
# ВАЖНО: только 1 воркер. Шедулер встроен в lifespan API через APScheduler —
# несколько воркеров = несколько шедулеров = дублирующиеся уведомления.
# Если потребуется масштабировать — см. 02_concurrent_price_checks.md §5.

[Install]
WantedBy=multi-user.target
```

### `/etc/systemd/system/ttt-bot.service`

```ini
[Unit]
Description=Track the Ticket Telegram bot
After=network.target ttt-api.service
Wants=ttt-api.service

[Service]
Type=simple
User=ttt
Group=ttt
WorkingDirectory=/home/ttt/app/services
EnvironmentFile=/etc/track-the-ticket/env
ExecStart=/home/ttt/app/.venv/bin/python -m bot
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ttt-api ttt-bot
sudo systemctl status ttt-api ttt-bot
```

---

## 9. Frontend build + nginx

### Билд фронта

`/home/ttt/app/frontend/.env.production`:

```
VITE_API_URL=https://api.<твой-домен>
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=track-the-ticket.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=track-the-ticket
VITE_FIREBASE_APP_ID=...
VITE_TELEGRAM_BOT_USERNAME=track_the_ticket_bot
```

```bash
cd /home/ttt/app/frontend
npm run build
# Результат в dist/
```

### nginx

`/etc/nginx/sites-available/ttt`:

```nginx
# Frontend (статика)
server {
    listen 80;
    server_name <твой-домен>;

    root /home/ttt/app/frontend/dist;
    index index.html;

    # SPA fallback — все unknown пути отдают index.html
    location / {
        try_files $uri /index.html;
    }

    # Раздаём скриншоты через API mount (см. services/api/main.py:67)
    # Если хочешь раздавать nginx-ом напрямую, проксируй /screenshots/ к API,
    # а не на файл-систему, потому что путь к ним идёт через DATABASE_PATH-aware код.
}

# API
server {
    listen 80;
    server_name api.<твой-домен>;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Долгие проверки цен могут занимать > минуты
        proxy_read_timeout 600s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ttt /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### HTTPS через Let's Encrypt

```bash
sudo certbot --nginx -d <домен> -d api.<домен>
# certbot сам пропишет редиректы и обновит конфиг nginx
```

---

## 10. Firebase Console — дополнительные настройки для прода

- Authentication → Settings → **Authorized domains**: добавить
  `<твой-домен>` (и при необходимости `api.<твой-домен>`).
- Скопировать актуальные `VITE_FIREBASE_*` значения из Project Settings
  → General → "Your apps" → SDK config в `.env.production` фронта.

---

## 11. Запуск и smoke-test

```bash
sudo systemctl restart ttt-api ttt-bot
sudo systemctl status ttt-api ttt-bot
curl https://api.<домен>/health        # ожидаем {"status":"ok"}
journalctl -u ttt-api -f                # смотрим, что шедулер пишет:
# Ожидаем строку вида:
# [scheduler] configured: daily at 07:00 and 17:00 Asia/Jerusalem
```

End-to-end:
1. Открыть `https://<домен>` → залогиниться Google.
2. Создать подписку из aviasales-ссылки.
3. Нажать "Sync" — должен прийти результат в Telegram (если бот привязан).
4. Дождаться 07:00 / 17:00 — должна сработать автоматическая проверка.

---

## 12. Бэкапы (минимум)

```bash
# Простой cron: ежедневный snapshot БД + screenshots
sudo crontab -e -u ttt
# 30 3 * * *  cp /var/lib/track-the-ticket/data/tracktheticket.db /var/lib/track-the-ticket/data/backup-$(date +\%Y\%m\%d).db && find /var/lib/track-the-ticket/data/ -name 'backup-*.db' -mtime +7 -delete
```

При появлении реальных юзеров — настроить Hetzner Storage Box или
rclone на S3-compatible хранилище.

---

## 13. Обновление (deploy нового кода)

```bash
ssh ttt@<vps>
cd ~/app
git pull
source .venv/bin/activate
pip install -r services/requirements.txt   # на случай новых зависимостей
cd frontend && npm ci && npm run build
sudo systemctl restart ttt-api ttt-bot
# Смотрим логи 30 секунд, ловим явные ошибки
journalctl -u ttt-api -u ttt-bot -n 50
```

Миграции БД сейчас ручные (Alembic не настроен — см.
[deployment_checklist.md](deployment_checklist.md) §7).

---

## 14. Что ещё стоит сделать после первого деплоя

- [ ] Sentry (или хотя бы алертинг в Telegram на стектрейс из логов).
- [ ] Поставить `fail2ban` для SSH.
- [ ] Отключить SSH password auth, оставить только ключи (`PasswordAuthentication no`).
- [ ] Убрать `ttt` из группы `sudo` после первоначального setup'а.
- [ ] Alembic — когда появятся реальные данные.
- [ ] Логи API в файл + ротация (`logrotate`), а не только journald.
