# ─────────────────────────────────────────────────────────────────────────────
# Track the Ticket — Messaging Module
# SQS queue (price-check tasks) + EventBridge rule (cron 3x/day)
# Schedule: 0 7,13,20 * * ? (UTC) = 09:00, 15:00, 22:00 Moscow time
# ─────────────────────────────────────────────────────────────────────────────
# TODO: TF-MESSAGING-01 — implement SQS + EventBridge + DLQ
