# Параллельные проверки цен (multi-user scaling)

> **Статус:** запланировано. Сейчас не реализуем — у проекта один активный
> пользователь, и последовательный прогон 1-3 подписок занимает 3-8 минут,
> что укладывается в слоты 07:00 / 17:00.
>
> **Триггер для возврата к задаче:** реальное число подписок (`SELECT COUNT(*)
> FROM subscriptions WHERE is_active = 1`) превысит 15-20, или утренний
> прогон начнёт пересекаться с дневным.

---

## Контекст

Сейчас [services/scheduler/jobs.py](../services/scheduler/jobs.py):
`run_all_active_checks()` идёт по подпискам **строго последовательно** —
один `check_price(sub_id)` за раз. Каждая проверка поднимает свой
Chromium через Playwright, гоняет 24-step replay (~2-3 мин) или
полный LLM-pipeline (~5-10 мин, редко).

**Грубая арифметика на 3-5 юзеров × 20 подписок ≈ 100 подписок:**

| Path | Время / проверка | Время на 100 (sequential) |
|---|---|---|
| Replay (горячая стратегия) | ~2.5 мин | **~4 ч** |
| LLM (холодный старт)       | ~7 мин   | ~12 ч (но это редкий путь) |

Утренний слот в 07:00 закончится после 11:00 — приемлемо.
Дневной в 17:00 закончится после 21:00 — уведомление приходит слишком
поздно, теряет смысл.

---

## Решение (когда реализуем)

Ввести **семафор** в `run_all_active_checks` ограничивающий число
одновременно бегущих `check_price`. Конкурентность настраивается env-
переменной с разумным дефолтом.

```python
# В services/scheduler/jobs.py
MAX_CONCURRENT_CHECKS = int(os.environ.get("MAX_CONCURRENT_CHECKS", "3"))

async def run_all_active_checks() -> None:
    with SessionLocal() as db:
        sub_ids = [s.id for s in db.query(Subscription)
                                   .filter(Subscription.is_active.is_(True)).all()]
    if not sub_ids:
        return

    sem = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

    async def _bounded(sid):
        async with sem:
            try:
                await check_price(sid)
            except Exception as exc:
                logger.error(f"[scheduler] sub={sid} failed: {exc}", exc_info=True)

    await asyncio.gather(*(_bounded(s) for s in sub_ids))
```

Время прогона при `MAX_CONCURRENT_CHECKS=3`:

| Подписок | Sequential | 3-параллельно |
|---|---|---|
| 20  | ~50 мин | ~17 мин |
| 60  | ~2.5 ч  | ~50 мин |
| 100 | ~4 ч    | ~85 мин |

---

## Что вокруг этого нужно проверить / поменять

### 1. Память VPS

Каждый параллельный Chromium держит ~300-500 МБ. Бюджет:

| Конкурентность | RAM на браузеры | Минимальная машина |
|---|---|---|
| 1 (сейчас) | ~500 МБ | Hetzner CX11 (2 ГБ) |
| 3          | ~1.5 ГБ | Hetzner CX22 (4 ГБ) |
| 5          | ~2.5 ГБ | Hetzner CX32 (8 ГБ) |

К этому прибавить ~1 ГБ на Python/API/SQLite/OS. Реальный
минимум на 3-параллель — **CX22 (4 ГБ)**, комфортно — **CX32 (8 ГБ)**.

### 2. Anthropic rate-limit

LLM-путь стучится в `claude-sonnet-4-X` через `verify_and_extract_price`
и vision-агентов. 3 параллельных проверки в LLM-режиме = ~3 одновременных
Sonnet-запроса с изображением. У стандартного tier лимит **5 RPM на
аккаунт**, так что 3 — безопасно. При повышении до 5-10 параллельных
проверок нужно либо запросить выше tier, либо ввести отдельный семафор
ТОЛЬКО для LLM-пути.

### 3. Одновременные записи в SQLite

`save_strategy`, `save_price_check`, `save_airline` пишут в одну БД-файл.
SQLite на write использует database-level lock. При 3-параллели
конфликт маловероятен (запись занимает миллисекунды), но при
конкуренции 10+ нужно либо `journal_mode=WAL` (легко включается
через `PRAGMA journal_mode=WAL` на старте), либо переезд на Postgres.

### 4. `services/run.py` остаётся single-worker

Шедулер живёт **внутри процесса API** через FastAPI lifespan.
Любое увеличение `uvicorn --workers N` сделает N независимых
шедулеров — проверки начнут дублироваться. Это нужно зафиксировать
комментарием в `run.py` сейчас, до того как кто-то добавит воркеры.
(См. также [03_hetzner_vps_deployment.md](03_hetzner_vps_deployment.md).)

### 5. Альтернатива (если будет ≥10 юзеров): вынести шедулер в отдельный процесс

`python -m scheduler` рядом с `bot/` — тогда API можно безопасно
поднимать в многоворкерном режиме. На сегодня это оверкилл.

---

## Чеклист реализации (когда взяться)

- [ ] Добавить `MAX_CONCURRENT_CHECKS` в `.env.example` (default 3).
- [ ] Переделать `run_all_active_checks` на `asyncio.Semaphore` +
      `asyncio.gather` (см. сниппет выше).
- [ ] Включить `PRAGMA journal_mode=WAL` в `common/database.py` через
      `event.listens_for(engine, "connect")`.
- [ ] Промерить реальное время прогона на 20-30 подписках — убедиться,
      что укладывается в час.
- [ ] Если VPS на CX11/CX22 — апгрейд до CX32 ДО включения параллели.
- [ ] Обновить чеклист деплоя: новая env-переменная, требования к RAM.
