import asyncio
import logging

import telegram

logger = logging.getLogger(__name__)


def post(message, bot_token, chat_id, photo=None):
    sent = asyncio.run(_send_telegram_async(message, bot_token, chat_id, photo))
    return sent


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
            logger.warning(f"Telegram timeout count: {retry_c}")
            pass
        except telegram.error.TelegramError as e:
            logger.error(f"Telegram error: {e}")
            break
        except FileNotFoundError:
            logger.error("Telegram module couldn't find an image to send.")
            break
        except Exception as err:
            logger.error(f"Unexpected Telegram error: {err}")
            break
        else:
            logger.info("Telegram message successfully sent.")
            return True
    return sent
