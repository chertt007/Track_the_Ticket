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

- **VPS:** существующий `ubuntu-4gb-hel1-1` (CX23: 2 vCPU, 4 GB RAM,
  40 GB SSD, Helsinki, IP `204.168.165.83`). Этого хватит для 1
  пользователя и до ~10 подписок с последовательными проверками.
  Когда включим параллель (см. [02_concurrent_price_checks.md](02_concurrent_price_checks.md))
  — отрескейлим в CX32 через Console за минуту.
- **Домен:** покупается отдельно (~$10/год). В плане ниже обозначен
  как `<домен>` — это полный домен второго уровня, напр. `tracktt.xyz`.
  Поддомены: `app.<домен>` для фронта, `api.<домен>` для бэка.
- **Образы:** хранятся в **GitHub Container Registry (ghcr.io)**,
  билдятся в GitHub Actions, бесплатно для приватных репо.

---

## Этапы (выполняем по порядку)

1. [Подготовка VPS](#1-подготовка-vps) — переустановка ОС, юзер `deploy`, Docker, ufw, fail2ban
2. ✅ [Покупка домена и DNS](#2-покупка-домена-и-dns) — A-записи на IP VPS
3. [Артефакты в репо](#3-артефакты-в-репо) — Dockerfile фронта, prod-compose, Caddyfile
4. [Секреты и `.env`](#4-секреты-и-env) — что и где лежит на VPS
5. [Firebase Console](#5-firebase-console) — Authorized domains
6. [Первый деплой вручную](#6-первый-деплой-вручную) — pull, build, up
7. [GitHub Actions CI/CD](#7-github-actions-cicd) — auto-deploy на push в main
8. [Бэкапы](#8-бэкапы) — volume snapshots + cron
9. [Hardening и observability](#9-hardening-и-observability) — fail2ban, логи, Sentry

---

## 1. Подготовка VPS

### ✅ 1.1. Переустановка ОС

Через Hetzner Cloud Console → сервер `ubuntu-4gb-hel1-1` → **Rebuild**
→ Ubuntu 24.04. Старые данные и снапшоты затрутся — убедиться, что
ничего важного на сервере нет.

После rebuild SSH-ключ из Cloud Console будет добавлен в `root` автоматически.

### ✅ 1.2. Базовая настройка

```bash
ssh root@204.168.165.83

# Обновление
apt update && apt upgrade -y

# Базовые пакеты
apt install -y ufw fail2ban ca-certificates curl gnupg

# Создаём непривилегированного пользователя для деплоя
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy

# Копируем ssh-ключ от root к deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

### ✅ 1.3. Docker

```bash
# Официальный Docker repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | tee /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Разрешаем deploy запускать docker без sudo
usermod -aG docker deploy

# Проверка
sudo -u deploy docker run --rm hello-world
```

### ✅ 1.4. Firewall

```bash
ufw allow OpenSSH
ufw allow 80/tcp     # HTTP (редирект и ACME challenge)
ufw allow 443/tcp    # HTTPS
ufw --force enable
ufw status
```

### ✅ 1.5. SSH hardening

В `/etc/ssh/sshd_config` (через `sudo nano` или sed):

```
PasswordAuthentication no
PermitRootLogin prohibit-password
```

```bash
systemctl restart ssh
```

После этого root-login по паролю выключен, остаётся только ключ.

---

## 2. Покупка домена и DNS

1. Купить домен у любого регистратора (Namecheap, Cloudflare Registrar,
   Porkbun). Для пет-проекта подходит `.xyz` / `.click` (~$1-3/год)
   или `.com` (~$10/год).
2. В DNS-настройках регистратора создать **две A-записи**:
   - `app.<домен>` → `204.168.165.83`
   - `api.<домен>` → `204.168.165.83`
   (Можно также корневой `<домен>` → IP, опционально.)
3. Подождать пропагации (обычно 5-30 минут). Проверка:
   ```bash
   dig +short app.<домен>
   # Должно вернуть 204.168.165.83
   ```

---

## 3. Артефакты в репо

Все эти файлы будем создавать **на следующем этапе**, после того как
VPS и домен готовы. Они коммитятся в репо — там нет секретов.

### 3.1. `services/Dockerfile` (уже есть, дополним)

Текущий Dockerfile собирает API. Бот будет использовать **тот же
образ**, но запускаться с другим `command` через compose. Возможно
понадобится докопировать `bot/` в образ.

### 3.2. `frontend/Dockerfile` (новый)

Multi-stage:
- Stage 1 (`node:20-alpine`): `npm ci && npm run build` → `dist/`
- Stage 2 (`nginx:alpine`): копирует `dist/` + минимальный nginx-конфиг
  с SPA fallback (`try_files $uri /index.html`).

Переменные `VITE_*` подставляются на этапе билда через `--build-arg`.
Они становятся частью JS-бандла и **не являются секретами в обычном смысле**
(Firebase API keys специально публичны, защита идёт через Authorized domains).

### 3.3. `docker-compose.prod.yml` (новый, в корне)

Четыре сервиса:
- **api** — образ из ghcr.io (`ghcr.io/<owner>/track-the-ticket-api:latest`),
  слушает `8000` *внутри* docker-сети, не пробрасывает наружу.
- **bot** — тот же образ, `command: python -m bot`, зависит от api.
- **frontend** — образ из ghcr.io (`ghcr.io/<owner>/track-the-ticket-frontend:latest`),
  слушает `80` *внутри* docker-сети.
- **caddy** — `caddy:2-alpine`, единственный сервис с пробросом
  портов 80/443 наружу. Читает `Caddyfile`, сам получает и продлевает
  Let's Encrypt сертификаты.

Volumes:
- `app_data` → `/data` (SQLite + screenshots, монтируется в api и bot)
- `caddy_data` → `/data` (сертификаты Caddy — важно сохранить, иначе
  при пересоздании контейнера Let's Encrypt может зарейтлимитить)
- `caddy_config` → `/config`

Все сервисы подключаются к одной сети `tttnet`.

### 3.4. `Caddyfile` (новый, в корне)

```
app.<домен> {
    reverse_proxy frontend:80
}

api.<домен> {
    reverse_proxy api:8000
    request_body {
        max_size 10MB
    }
}
```

Caddy сам выпустит сертификаты при первом запросе и будет продлевать
автоматически. Никакого certbot.

### 3.5. `.env.prod.example` (новый, в корне)

Шаблон без секретов, коммитится в репо. Реальный `.env` создаётся
только на VPS (см. §4).

---

## 4. Секреты и `.env`

На VPS:

```bash
sudo -u deploy mkdir -p /home/deploy/track-the-ticket
cd /home/deploy/track-the-ticket
```

Сюда кладём:
- `.env` (mode 600, owner deploy) — заполнен по `.env.prod.example`
- `firebase-sa.json` (mode 600) — Firebase Admin service account
- `docker-compose.prod.yml` (копия из репо)
- `Caddyfile` (копия из репо)

`.env` содержит:

```bash
# Где живут данные внутри volume
DATABASE_PATH=/data/tracktheticket.db
SCREENSHOTS_DIR=/data/screenshots

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/run/secrets/firebase-sa.json

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=track_the_ticket_bot
TELEGRAM_INTERNAL_SECRET=<openssl rand -hex 32>
API_BASE_URL=http://api:8000

# Домен (для CORS и Caddy)
DOMAIN=<домен>
```

`firebase-sa.json` монтируется как read-only bind в api и bot:
```yaml
volumes:
  - ./firebase-sa.json:/run/secrets/firebase-sa.json:ro
```

---

## 5. Firebase Console

Authentication → Settings → **Authorized domains** — добавить:
- `app.<домен>`
- (опционально) `<домен>`

Скопировать актуальные `VITE_FIREBASE_*` значения из Project Settings
→ General → "Your apps" → SDK config. Они нужны для GitHub Actions
секретов (см. §7) — будут переданы как build-args в образ фронта.

---

## 6. Первый деплой вручную

```bash
ssh deploy@204.168.165.83
cd ~/track-the-ticket

# Логинимся в ghcr.io (нужен Personal Access Token с read:packages)
echo <GHCR_TOKEN> | docker login ghcr.io -u <github-username> --password-stdin

# Тянем образы (предполагаем, что GitHub Actions уже их собрал и запушил —
# либо делаем первый билд локально и пушим, либо триггерим workflow вручную)
docker compose -f docker-compose.prod.yml pull

# Стартуем
docker compose -f docker-compose.prod.yml up -d

# Логи
docker compose -f docker-compose.prod.yml logs -f
```

### Smoke-test
- `https://app.<домен>` → открывается фронт, Google login работает
- `https://api.<домен>/health` → `{"status":"ok"}`
- Создать подписку → нажать Sync → результат приходит в Telegram
- `docker compose logs api` → ловим строку `[scheduler] configured: daily at 07:00 and 17:00`

---

## 7. GitHub Actions CI/CD

### 7.1. Что делает workflow

На push в `main`:
1. Build образа api → push в `ghcr.io/<owner>/track-the-ticket-api:latest` + `:<sha>`
2. Build образа frontend (с `VITE_*` build-args из GitHub Secrets) → push в `ghcr.io/.../frontend`
3. SSH на VPS, `cd ~/track-the-ticket`, `docker compose pull && docker compose up -d`
4. Проверка health, при ошибке — exit code != 0, workflow красный

### 7.2. GitHub Secrets, которые нужны

В **Settings → Secrets and variables → Actions**:

- `VPS_HOST` = `204.168.165.83`
- `VPS_USER` = `deploy`
- `VPS_SSH_KEY` = приватный SSH-ключ (тот, чей публичный лежит в
  `/home/deploy/.ssh/authorized_keys`). Сгенерировать отдельную пару
  специально для CI:
  ```bash
  ssh-keygen -t ed25519 -f ttt-deploy -N ""
  ```
  Публичный — на VPS, приватный — в GitHub Secret.
- `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`,
  `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID`,
  `VITE_TELEGRAM_BOT_USERNAME`, `VITE_API_URL` (=`https://api.<домен>`)
  — build-args для фронта.

`GITHUB_TOKEN` (для пуша в ghcr.io) предоставляется автоматически.

### 7.3. Файл workflow

`.github/workflows/deploy.yml` — создаём на соответствующем шаге.
Использует `docker/build-push-action` и `appleboy/ssh-action`.

---

## 8. Бэкапы

Volume `app_data` живёт в `/var/lib/docker/volumes/track-the-ticket_app_data/_data/`.

Простой cron под `deploy`:

```bash
crontab -e
# Ежедневно в 03:30 — snapshot SQLite + retention 7 дней
30 3 * * *  docker run --rm -v track-the-ticket_app_data:/data -v /home/deploy/backups:/backup alpine sh -c "cp /data/tracktheticket.db /backup/db-$(date +\%Y\%m\%d).db && find /backup -name 'db-*.db' -mtime +7 -delete"
```

Когда появятся реальные юзеры — Hetzner Storage Box / S3 + rclone.

---

## 9. Hardening и observability

- [ ] `fail2ban` уже стоит после §1 — проверить `systemctl status fail2ban`
- [ ] Sentry или алерт в Telegram на ERROR из логов
- [ ] `docker logs` с rotation: в `/etc/docker/daemon.json`:
  ```json
  { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
  ```
  потом `systemctl restart docker`
- [ ] Снять `deploy` из группы `sudo` после полной настройки
  (если нужны редкие админ-задачи — `su` под root по ssh-ключу)
- [ ] Alembic для миграций БД — когда появятся реальные данные
- [ ] Мониторинг диска: Playwright Chromium + screenshots могут расти

---

## Что НЕ входит в этот план

- Postgres — пока остаёмся на SQLite, переход — отдельная задача
- Параллельные проверки цен — план [02_concurrent_price_checks.md](02_concurrent_price_checks.md)
- Staging-окружение — у нас одна среда, прод. Если понадобится stg —
  второй compose-файл с другим доменом и другими volume-name'ами.
