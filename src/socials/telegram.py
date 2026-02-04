"""socials/telegram.py: Interface for sending notifications to Telegram."""

import asyncio
import logging

import telegram

logger = logging.getLogger(__name__)


def post(message, bot_token, chat_id, photo=None):
    """Send a message and optional photo to Telegram.

    :param message: The text content or caption.
    :param bot_token: Telegram bot token.
    :param chat_id: Target chat or channel ID.
    :param photo: File-like object or path to a photo.
    :return: True if sent successfully, False otherwise.
    """
    return asyncio.run(_send_telegram_async(message, bot_token, chat_id, photo))


async def _send_telegram_async(message, bot_token, chat_id, photo=None):
    sent = False
    retry_c = 0
    while not sent:
        try:
            if photo and hasattr(photo, "seek"):
                photo.seek(0)
            bot = telegram.Bot(token=bot_token)
            if photo:
                sent = await bot.send_photo(
                    chat_id=chat_id, photo=photo, caption=message
                )
            else:
                sent = await bot.send_message(chat_id=chat_id, text=message)
        except telegram.error.TimedOut:
            retry_c += 1
            logger.warning("Telegram timeout count: %s", retry_c)
        except telegram.error.TelegramError as e:
            logger.exception("Telegram error: %s", e)
            break
        except FileNotFoundError:
            logger.exception("Telegram module couldn't find an image to send.")
            break
        except Exception as err:
            logger.exception("Unexpected Telegram error: %s", err)
            break
        else:
            logger.info("Telegram message successfully sent.")
            return True
    return sent
