"""
Telegram delivery for price-check outcomes.

After every successful `_save_check_result` (replay or LLM path) we send
the user a `sendPhoto` with the final-page screenshot and a caption that
summarises route, airline, date, time and price.

Failure modes (network errors, 4xx/5xx from Telegram, missing chat link)
are logged but never raised — a missed notification must not crash the
price-check pipeline. The `price_checks` row is already persisted by the
time we get here, so the data is safe regardless of delivery success.
"""
from __future__ import annotations

import html
import logging
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, Protocol

import httpx

from common.database import SessionLocal
from common.queries import get_user

logger = logging.getLogger(__name__)


# Currency code → display symbol used in captions. Anything not in the
# map falls back to the ISO code itself (e.g. "13764 RUB").
_CURRENCY_SYMBOLS: dict[str, str] = {
    "RUB": "₽",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "ILS": "₪",
    "KZT": "₸",
    "UAH": "₴",
}


class _PriceLike(Protocol):
    amount: Decimal
    currency: str


class _JobLike(Protocol):
    subscription_id: str
    airline_name: str
    origin: str
    destination: str
    departure_date: str
    departure_time: str


def _format_amount(amount: Decimal) -> str:
    """Render a price the same way Telegram captions look elsewhere: no
    trailing zeros for whole numbers, two-decimals for fractional."""
    if amount == amount.to_integral_value():
        return f"{int(amount):,}".replace(",", " ")  # narrow no-break space
    return f"{amount:,.2f}".replace(",", " ")


def _format_caption(job: _JobLike, price: Optional[_PriceLike]) -> str:
    """Build the HTML caption sent to Telegram."""
    checked_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    header = (
        f"✈️ <b>{html.escape(job.origin)} → {html.escape(job.destination)}</b>\n"
        f"{html.escape(job.airline_name)} · {html.escape(job.departure_date)}"
        f" · {html.escape(job.departure_time)}"
    )
    if price is None:
        body = "\n\n⚠️ Цену не удалось считать"
    else:
        symbol = _CURRENCY_SYMBOLS.get(price.currency, price.currency)
        body = f"\n\n💵 <b>{_format_amount(price.amount)} {symbol}</b>"
    footer = f"\n🕐 Проверено: {checked_at}"
    return header + body + footer


async def send_check_result(
    user_id: str,
    job: _JobLike,
    price: Optional[_PriceLike],
    screenshot_path: Path,
) -> None:
    """
    Send the user a Telegram message with the final screenshot and price.

    No-op (with a log line) when:
      - TELEGRAM_BOT_TOKEN is not configured;
      - the user has no `telegram_chat_id` (never linked, or unlinked);
      - the screenshot file is missing.

    Errors from the Telegram API and the network are logged but never
    raised — see module docstring.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("[notifier] TELEGRAM_BOT_TOKEN not set — skipping")
        return

    with SessionLocal() as db:
        user = get_user(db, user_id)
        if user is None or user.telegram_chat_id is None:
            logger.info(f"[notifier] user {user_id} not linked, skip")
            return
        chat_id = user.telegram_chat_id

    if not screenshot_path.exists():
        logger.warning(
            f"[notifier] screenshot {screenshot_path} missing — sending text-only fallback"
        )
        await _send_text_fallback(bot_token, chat_id, job, price)
        return

    caption = _format_caption(job, price)
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with screenshot_path.open("rb") as fh:
                response = await client.post(
                    url,
                    data={
                        "chat_id":    str(chat_id),
                        "caption":    caption,
                        "parse_mode": "HTML",
                    },
                    files={"photo": (screenshot_path.name, fh, "image/jpeg")},
                )
    except httpx.HTTPError as exc:
        logger.error(f"[notifier] sendPhoto transport error: {exc}")
        return

    if response.status_code == 200:
        logger.info(
            f"[notifier] sub={job.subscription_id} delivered to chat={chat_id} "
            f"price={price.amount if price else None}"
        )
        return

    # On 403 the user blocked the bot or deleted the chat. Per product
    # decision we keep `users.telegram_chat_id` as-is so the link survives
    # an accidental block — the user can re-add the bot and notifications
    # resume. Just log and move on.
    if response.status_code == 403:
        logger.warning(
            f"[notifier] sub={job.subscription_id} chat={chat_id} returned 403 "
            f"(bot blocked or chat deleted) — keeping link, suppressing"
        )
        return

    logger.error(
        f"[notifier] sub={job.subscription_id} sendPhoto http={response.status_code} "
        f"body={response.text[:300]}"
    )


async def _send_text_fallback(
    bot_token: str,
    chat_id: int,
    job: _JobLike,
    price: Optional[_PriceLike],
) -> None:
    """When the screenshot file is gone, deliver just the caption."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={
                    "chat_id":    str(chat_id),
                    "text":       _format_caption(job, price),
                    "parse_mode": "HTML",
                },
            )
    except httpx.HTTPError as exc:
        logger.error(f"[notifier] sendMessage transport error: {exc}")
        return
    if response.status_code != 200:
        logger.error(
            f"[notifier] sendMessage http={response.status_code} body={response.text[:300]}"
        )
