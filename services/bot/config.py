"""Environment-driven config for the Telegram bot."""
import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set — check the project root .env")
    return value


# Bot identity (BotFather)
TELEGRAM_BOT_TOKEN    = _required("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")  # cosmetic only

# How the bot talks back to the API for /telegram/claim
API_BASE_URL             = os.environ.get("API_BASE_URL", "http://localhost:8000")
TELEGRAM_INTERNAL_SECRET = _required("TELEGRAM_INTERNAL_SECRET")
