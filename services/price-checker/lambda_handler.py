"""
Price-checker Lambda handler.
Triggered by EventBridge cron: 08:00, 16:00, 21:00 Israel time (UTC+3).
Iterates all active subscriptions sequentially and checks current prices.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import boto3
import httpx

from agent import check_price

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

INTERNAL_API_URL = os.environ["INTERNAL_API_URL"]      # e.g. https://api.tracktheticket.com
INTERNAL_API_TOKEN = os.environ["INTERNAL_API_TOKEN"]
SCREENSHOTS_BUCKET = os.environ["SCREENSHOTS_BUCKET"]

s3 = boto3.client("s3")


def lambda_handler(event: dict, context) -> dict:
    logger.info("price-checker started", extra={"event": event})
    asyncio.run(_run())
    return {"statusCode": 200, "body": "done"}


async def _run() -> None:
    subscriptions = await _fetch_active_subscriptions()
    logger.info(f"processing {len(subscriptions)} subscriptions")

    for sub in subscriptions:
        try:
            await _process_subscription(sub)
        except Exception as exc:
            logger.error(
                f"failed to process subscription {sub['id']}: {exc}",
                exc_info=True,
            )


async def _fetch_active_subscriptions() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{INTERNAL_API_URL}/internal/subscriptions/active",
            headers={"X-Internal-Token": INTERNAL_API_TOKEN},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def _process_subscription(sub: dict) -> None:
    sub_id = sub["id"]
    logger.info(f"checking price for subscription {sub_id}")

    result = await check_price(
        airline_domain=sub["airline_domain"],
        origin_iata=sub["origin_iata"],
        destination_iata=sub["destination_iata"],
        departure_date=sub["departure_date"],
        flight_number=sub["flight_number"],
        with_baggage=sub.get("baggage_info") not in (None, "", "none", "без багажа"),
    )

    logger.info(
        f"subscription {sub_id}: price={result.price} {result.currency} flight={result.flight_number}"
    )

    # Upload screenshot to S3 if available
    s3_key = None
    if result.screenshot_base64:
        s3_key = _upload_screenshot(sub_id, result.screenshot_base64)

    # Save price record to DB via internal API
    await _save_price_record(sub_id, result, s3_key)

    # Send Telegram notification (always, not only on price change)
    if sub.get("telegram_id"):
        await _send_telegram(sub, result, s3_key)


def _upload_screenshot(sub_id: int, screenshot_b64: str) -> str:
    import base64

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    key = f"screenshots/{sub_id}/{timestamp}.png"
    image_bytes = base64.b64decode(screenshot_b64)
    s3.put_object(
        Bucket=SCREENSHOTS_BUCKET,
        Key=key,
        Body=image_bytes,
        ContentType="image/png",
    )
    logger.info(f"screenshot uploaded: {key}")
    return key


async def _save_price_record(sub_id: int, result, s3_key: str | None) -> None:
    payload = {
        "price": result.price,
        "currency": result.currency,
        "s3_key": s3_key,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if result.price > 0 else "no_price",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{INTERNAL_API_URL}/internal/subscriptions/{sub_id}/prices",
            headers={"X-Internal-Token": INTERNAL_API_TOKEN},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()


async def _send_telegram(sub: dict, result, s3_key: str | None) -> None:
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not telegram_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
        return

    chat_id = sub["telegram_id"]
    route = f"{sub['origin_iata']} → {sub['destination_iata']}"
    date = sub["departure_date"]
    flight = result.flight_number or sub["flight_number"]
    price_str = f"{result.price} {result.currency}" if result.price else "N/A"

    text = (
        f"✈️ *{route}* — {date}\n"
        f"Рейс: {flight}\n"
        f"Цена: *{price_str}*"
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{telegram_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    logger.info(f"telegram notification sent to {chat_id}")
