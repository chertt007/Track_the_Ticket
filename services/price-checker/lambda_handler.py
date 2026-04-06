"""
Price-checker Lambda handler.

Supports two invocation modes:

1. SQS trigger (manual check from API or one-off scheduled):
   Each SQS record body: {"subscription_id": <int>}
   Processes only the subscriptions listed in the SQS messages.

2. EventBridge direct trigger (scheduled cron, 3×/day):
   Event does NOT contain "Records" key.
   Fetches all active subscriptions from DB and processes them sequentially.
"""

import asyncio
import base64
import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import asyncpg
import boto3

from agent import run_price_check, _is_agent_failure

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ── DB connection ─────────────────────────────────────────────────────────────

async def _get_db_conn() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
    )


# ── S3 screenshot upload ──────────────────────────────────────────────────────

def _upload_screenshot(screenshot_b64: str, subscription_id: int, timestamp: str) -> str | None:
    """Upload base64 PNG to S3. Returns s3_key or None on failure."""
    bucket = os.environ.get("SCREENSHOTS_BUCKET", "")
    region = os.environ.get("AWS_REGION", "us-east-1")
    if not bucket:
        logger.warning("SCREENSHOTS_BUCKET not set — skipping screenshot upload")
        return None
    try:
        img_bytes = base64.b64decode(screenshot_b64)
        key = f"screenshots/{subscription_id}/{timestamp}.png"
        boto3.client("s3", region_name=region).put_object(
            Bucket=bucket,
            Key=key,
            Body=img_bytes,
            ContentType="image/png",
        )
        logger.info(f"screenshot uploaded: {key}")
        return key
    except Exception as exc:
        logger.warning(f"S3 screenshot upload failed: {exc}")
        return None


# ── Core: process one subscription ───────────────────────────────────────────

async def _process_subscription(subscription_id: int) -> None:
    """Read subscription, run price check, write result to DB."""
    logger.info(f"processing subscription_id={subscription_id}")
    conn = await _get_db_conn()
    logger.info(f"db connected for subscription_id={subscription_id}")
    try:
        # Read subscription
        row = await conn.fetchrow(
            """
            SELECT id, airline, airline_iata, airline_domain,
                   origin_iata, destination_iata, departure_date,
                   flight_number, baggage_info, is_active
            FROM subscriptions
            WHERE id = $1
            """,
            subscription_id,
        )

        if not row:
            logger.warning(f"subscription {subscription_id} not found — skipping")
            return

        if not row["is_active"]:
            logger.info(f"subscription {subscription_id} is inactive — skipping")
            return

        # Run price check
        with_baggage = row["baggage_info"] not in (None, "", "no_baggage")
        result = await run_price_check(
            airline_name=row["airline"] or "",
            airline_iata=row["airline_iata"] or "",
            origin_iata=row["origin_iata"],
            destination_iata=row["destination_iata"],
            departure_date=str(row["departure_date"]),
            flight_number=row["flight_number"] or "",
            with_baggage=with_baggage,
        )

        # Determine record status
        if result.price > 0:
            check_status = "ok"
        elif _is_agent_failure(result.raw_output):
            check_status = "agent_error"
        else:
            check_status = "no_price"

        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Upload screenshot to S3
        s3_key: str | None = None
        if result.screenshot_b64:
            s3_key = _upload_screenshot(result.screenshot_b64, subscription_id, timestamp)

        # Persist price_history record
        await conn.execute(
            """
            INSERT INTO price_history (subscription_id, price, currency, s3_key, status, checked_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            subscription_id,
            Decimal(str(result.price)),
            result.currency,
            s3_key,
            check_status,
            now,
        )

        # Update subscription: last_checked_at and optionally cache airline_domain
        if result.domain_used and not row["airline_domain"]:
            await conn.execute(
                "UPDATE subscriptions SET last_checked_at = $1, airline_domain = $2 WHERE id = $3",
                now,
                result.domain_used,
                subscription_id,
            )
        else:
            await conn.execute(
                "UPDATE subscriptions SET last_checked_at = $1 WHERE id = $2",
                now,
                subscription_id,
            )

        logger.info(
            "price check done",
            extra={
                "subscription_id": subscription_id,
                "price": result.price,
                "currency": result.currency,
                "status": check_status,
                "s3_key": s3_key,
            },
        )

    finally:
        await conn.close()


# ── Scheduled run: all active subscriptions ───────────────────────────────────

async def _process_all_active() -> None:
    """Fetch all active subscriptions from DB and process them sequentially."""
    conn = await _get_db_conn()
    try:
        rows = await conn.fetch(
            "SELECT id FROM subscriptions WHERE is_active = true ORDER BY id"
        )
    finally:
        await conn.close()

    logger.info(f"scheduled run: processing {len(rows)} active subscriptions")

    for row in rows:
        try:
            await _process_subscription(row["id"])
        except Exception as exc:
            logger.error(
                f"failed to process subscription {row['id']}: {exc}",
                exc_info=True,
            )
            # Continue with next subscription even if one fails


# ── Lambda entry point ────────────────────────────────────────────────────────

def handler(event: dict, context: object) -> dict:
    """
    Unified Lambda handler for two invocation types:

    SQS (manual check or one-off):
        event = {"Records": [{"body": '{"subscription_id": 5}'}, ...]}

    EventBridge (scheduled cron):
        event = {"source": "aws.events", ...} — no "Records" key
    """
    records = event.get("Records", [])

    if records:
        # SQS mode: process specific subscriptions from queue messages
        logger.info(f"SQS trigger: processing {len(records)} record(s)")
        for record in records:
            try:
                body = json.loads(record["body"])
                subscription_id = int(body["subscription_id"])
                asyncio.run(_process_subscription(subscription_id))
            except Exception as exc:
                logger.error(f"failed to process SQS record: {exc}", exc_info=True)
                # Re-raise so the message goes to DLQ after max receive count
                raise
    else:
        # EventBridge mode: process all active subscriptions
        logger.info("EventBridge trigger: running scheduled price check for all active subscriptions")
        asyncio.run(_process_all_active())

    return {"statusCode": 200}
