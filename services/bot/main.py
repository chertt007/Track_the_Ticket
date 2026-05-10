"""Telegram bot entrypoint — long-polling Application."""
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load env from project root before importing config (which reads env vars).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from common.logging_config import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)

from telegram.ext import Application, CommandHandler  # noqa: E402

from . import config  # noqa: E402
from .handlers import start, status, unlink  # noqa: E402


def run() -> None:
    display_name = (config.TELEGRAM_BOT_USERNAME or "<unknown>").lstrip("@")
    logger.info(f"[bot] starting polling for @{display_name}")
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("unlink", unlink))
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    run()
