"""Telegram command handlers."""
import logging
from typing import Final

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from . import config

logger = logging.getLogger(__name__)

# Reply texts. RU only for now (matches Stage 6 caption locale policy).
_WELCOME: Final = (
    "👋 Привет! Я бот <b>Track the Ticket</b>.\n\n"
    "Я присылаю уведомления о ценах на твои подписки рейсов.\n"
    "Чтобы подключить аккаунт — открой сайт, нажми "
    "«Подключить Telegram» и пройди по сгенерированной ссылке."
)

_CLAIM_MESSAGES: Final = {
    "ok":           "✅ Подключено! Теперь я буду присылать сюда результаты проверок цен.",
    "expired":      "⏱ Ссылка истекла. Сгенерируй новую на сайте.",
    "already_used": "Эта ссылка уже использована. Если нужно перепривязать — сгенерируй новую на сайте.",
    "not_found":    "Ссылка не найдена. Возможно, ты вставил её не полностью.",
}
_CLAIM_FALLBACK: Final = "Не получилось подключить. Попробуй сгенерировать новую ссылку на сайте."

_STATUS: Final = (
    "Статус привязки удобнее посмотреть на сайте — раздел настроек, пункт «Telegram».\n"
    "Если я уже отправлял сюда подтверждение «✅ Подключено» — значит, всё работает."
)

_UNLINK_HINT: Final = (
    "Отвязать аккаунт можно на сайте: настройки → «Telegram» → «Отвязать».\n"
    "Так связь точно разорвётся для обеих сторон."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start handler.

    With no argument — show a welcome message. With a deep-link token (from
    https://t.me/<bot>?start=<token>) — call the API to redeem it and report
    the outcome to the user.
    """
    chat = update.effective_chat
    if chat is None:
        return

    if not context.args:
        await chat.send_message(_WELCOME, parse_mode="HTML")
        return

    token = context.args[0]
    chat_id = chat.id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{config.API_BASE_URL}/telegram/claim",
                json={"token": token, "chat_id": chat_id},
                headers={"X-Internal-Secret": config.TELEGRAM_INTERNAL_SECRET},
            )
    except httpx.HTTPError as exc:
        logger.error(f"[bot] claim transport error: {exc}")
        await chat.send_message(_CLAIM_FALLBACK)
        return

    if r.status_code != 200:
        logger.warning(f"[bot] claim http {r.status_code}: {r.text}")
        await chat.send_message(_CLAIM_FALLBACK)
        return

    body = r.json()
    reason = body.get("message", "")
    text = _CLAIM_MESSAGES.get(reason, _CLAIM_FALLBACK)
    logger.info(f"[bot] /start claim chat_id={chat_id} ok={body.get('ok')} reason={reason}")
    await chat.send_message(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await chat.send_message(_STATUS)


async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await chat.send_message(_UNLINK_HINT)
