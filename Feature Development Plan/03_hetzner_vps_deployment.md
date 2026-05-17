# Деплой на Hetzner VPS (Docker + GitHub Actions)

> **Цель этого документа:** пошаговый план переноса Track the Ticket
> на существующую VPS Hetzner с использованием Docker Compose,
> автоматическим HTTPS через Caddy и авто-деплоем по push в `main`
> через GitHub Actions.
>
> Общий чеклист переменных/секретов смотри в
> [deployment_checklist.md](deployment_checklist.md) — этот файл его
> *дополняет* провайдер-специфичными шагами.

---

## Целевая архитектура

```
                    Internet
                       │
                       ▼ :443
              ┌─────────────────┐
              │      Caddy      │  ← TLS termination, авто Let's Encrypt
              │   (Docker)      │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   app.domain   api.domain      (internal)
   ┌─────────┐  ┌─────────┐    ┌─────────┐
   │frontend │  │   api   │◄───┤   bot   │
   │ nginx + │  │ FastAPI │    │aiogram  │
   │static   │  │+Playwr. │    │         │
   └─────────┘  └────┬────┘    └────┬────┘
                     │              │
                     ▼              │
              ┌────────────┐ ◄──────┘
              │  volumes   │
              │ data/      │ ← SQLite + screenshots
              └────────────┘
```

Всё крутится в Docker. На хосте — только `docker`, `ufw`, `fail2ban`.
Никакого Python/Node/nginx на самом хосте.

---

## Используемые ресурсы

- **VPS:** `ubuntu-4gb-hel1-1` (CX23: 2 vCPU, 4 GB RAM, 40 GB SSD,
  Helsinki, IP `204.168.165.83`). Ubuntu 24.04 LTS. Хватит для 1
  пользователя и до ~10 подписок с последовательными проверками.
- **Домен:** `track-the-ticket.com` куплен на Cloudflare.
  Поддомены: `app.track-the-ticket.com` (фронт), `api.track-the-ticket.com` (API).
- **Образы:** хранятся в **GitHub Container Registry (ghcr.io)**,
  билдятся в GitHub Actions, бесплатно для публичных репо.

---

## Этапы

1. ✅ [Подготовка VPS](#1-подготовка-vps)
2. ✅ [Покупка домена и DNS](#2-покупка-домена-и-dns)
3. ✅ [Артефакты в репо](#3-артефакты-в-репо)
4. ✅ [GitHub Actions CI/CD — secrets](#4-github-actions-cicd)
5. ✅ [Секреты и `.env` на VPS](#5-секреты-и-env-на-vps)
6. ✅ [Firebase Console — Authorized domains](#6-firebase-console)
7. ⬜ [Первый деплой вручную](#7-первый-деплой-вручную)
8. ⬜ [Бэкапы](#8-бэкапы)
9. ⬜ [Hardening и observability](#9-hardening-и-observability)

---

## 1. Подготовка VPS

### ✅ 1.1. Переустановка ОС
Rebuild через Hetzner Console → Ubuntu 24.04.

### ✅ 1.2. Базовая настройка
- `apt update && apt upgrade -y`
- Пользователь `deploy` создан
- SSH-ключ `work_pc` (личный) добавлен в `/root/.ssh/` и `/home/deploy/.ssh/`
- SSH-ключ `ttt-deploy` (CI) добавлен в `/home/deploy/.ssh/authorized_keys`
- `PasswordAuthentication no` в sshd_config

### ✅ 1.3. Docker
Docker CE + Compose plugin установлены. `deploy` добавлен в группу `docker`.

### ✅ 1.4. Firewall
ufw активен: открыты только 22 (SSH), 80 (HTTP), 443 (HTTPS).

### ✅ 1.5. fail2ban
Установлен и запущен.

### ✅ 1.6. Папка приложения
`/home/deploy/track-the-ticket/` создана.

---

## 2. Покупка домена и DNS

### ✅ Домен
`track-the-ticket.com` зарегистрирован на Cloudflare Registrar.

### ✅ DNS-записи
В Cloudflare DNS добавлены две A-записи (DNS only, не проксируется):
- `app.track-the-ticket.com` → `204.168.165.83`
- `api.track-the-ticket.com` → `204.168.165.83`

---

## 3. Артефакты в репо

### ✅ Созданные файлы

| Файл | Назначение |
|------|-----------|
| `services/Dockerfile` | Дополнен: добавлены `bot/`, `notifier/`, `scheduler/`, `agents/`, `price_checker/` |
| `frontend/Dockerfile` | Multi-stage: node билдит → nginx раздаёт статику |
| `frontend/nginx.conf` | SPA fallback для React Router |
| `docker-compose.prod.yml` | 4 сервиса: caddy, api, bot, frontend |
| `Caddyfile` | Маршрутизация по поддоменам + авто HTTPS |
| `.env.prod.example` | Шаблон секретов (без реальных значений) |
| `.github/workflows/deploy.yml` | CI/CD: build → push ghcr.io → SSH deploy |

---

## 4. GitHub Actions CI/CD

### ✅ GitHub Secrets добавлены
В репозитории → Settings → Secrets → Actions:

| Secret | Значение |
|--------|---------|
| `VPS_HOST` | `204.168.165.83` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | приватный ключ `ttt-deploy` |
| `VITE_API_URL` | `https://api.track-the-ticket.com` |
| `VITE_FIREBASE_API_KEY` | из Firebase Console |
| `VITE_FIREBASE_AUTH_DOMAIN` | из Firebase Console |
| `VITE_FIREBASE_PROJECT_ID` | из Firebase Console |
| `VITE_FIREBASE_APP_ID` | из Firebase Console |
| `VITE_TELEGRAM_BOT_USERNAME` | имя бота без @ |

---

## 5. Секреты и `.env` на VPS

**Следующий шаг при продолжении работы.**

На VPS под пользователем `deploy` в папке `~/track-the-ticket/` нужно создать:

### 5.1. Файл `.env`

```bash
ssh deploy@204.168.165.83
cd ~/track-the-ticket
nano .env
```

Содержимое (заполнить по `.env.prod.example`):

```bash
# Docker image prefix — lowercase!
# Узнать: echo "ghcr.io/$(echo YOUR_GITHUB_USERNAME | tr '[:upper:]' '[:lower:]')/track-the-ticket"
IMAGE_PREFIX=ghcr.io/<github-username-lowercase>/track-the-ticket

DATABASE_PATH=/data/tracktheticket.db
SCREENSHOTS_DIR=/data/screenshots

FIREBASE_SERVICE_ACCOUNT_PATH=/run/secrets/firebase-sa.json

ANTHROPIC_API_KEY=sk-ant-...

TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=track_the_ticket_bot
TELEGRAM_INTERNAL_SECRET=<openssl rand -hex 32 на локалке>
API_BASE_URL=http://api:8000
```

```bash
chmod 600 .env
```

### 5.2. Firebase service account

Скачать из Firebase Console → Project Settings → Service accounts →
Generate new private key. Загрузить на VPS:

```powershell
# На локалке в PowerShell:
scp C:\path\to\firebase-sa.json deploy@204.168.165.83:~/track-the-ticket/firebase-sa.json
```

```bash
# На VPS:
chmod 600 ~/track-the-ticket/firebase-sa.json
```

### 5.3. Скопировать compose и Caddyfile

После коммита артефактов в репо — скопировать на VPS:

```powershell
scp docker-compose.prod.yml deploy@204.168.165.83:~/track-the-ticket/
scp Caddyfile deploy@204.168.165.83:~/track-the-ticket/
```

---

## 6. Firebase Console

Authentication → Settings → **Authorized domains** → Add domain:
- `app.track-the-ticket.com`

---

## 7. Первый деплой вручную

Сначала сделать push в `main` — GitHub Actions соберёт образы и запушит
в ghcr.io. Затем на VPS:

```bash
ssh deploy@204.168.165.83
cd ~/track-the-ticket
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

### Smoke-test
```bash
curl https://api.track-the-ticket.com/health   # ожидаем {"status":"ok"}
```
- Открыть `https://app.track-the-ticket.com` → Google login работает
- Создать подписку → Sync → приходит уведомление в Telegram
- `docker compose logs api` → строка `[scheduler] configured: daily at 07:00 and 17:00`

---

## 8. Бэкапы

```bash
ssh deploy@204.168.165.83
crontab -e
```

Добавить строку:
```
30 3 * * *  docker run --rm -v track-the-ticket_app_data:/data -v /home/deploy/backups:/backup alpine sh -c "cp /data/tracktheticket.db /backup/db-$(date +\%Y\%m\%d).db && find /backup -name 'db-*.db' -mtime +7 -delete"
```

---

## 9. Hardening и observability

- [ ] Docker log rotation — в `/etc/docker/daemon.json`:
  ```json
  { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
  ```
  потом `systemctl restart docker`
- [ ] Sentry или алерт в Telegram на ERROR из логов
- [ ] Снять `deploy` из группы `sudo` после полной настройки
- [ ] Alembic для миграций БД — когда появятся реальные данные
- [ ] Мониторинг диска: Playwright Chromium + screenshots могут расти

---

## Что НЕ входит в этот план

- Postgres — пока остаёмся на SQLite, переход — отдельная задача
- Параллельные проверки цен — план [02_concurrent_price_checks.md](02_concurrent_price_checks.md)
- Staging-окружение — у нас одна среда, прод
