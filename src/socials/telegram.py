import asyncio

import telegram


import logging

logger = logging.getLogger(__name__)


def post(message, config, photo=None):
    return asyncio.run(telegram_send(message, config, photo))


async def telegram_send(message, config, photo=None):
    sent = False
    retry_c = 0
    while sent == False:
        try:
            bot = telegram.Bot(token=config.get("TELEGRAM", "BOT_TOKEN"))
            if photo:
                sent = await bot.send_photo(
                    chat_id=config.get("TELEGRAM", "ROOM_ID"),
                    photo=photo,
                    caption=message,
                )
            else:
                sent = await bot.send_message(
                    chat_id=config.get("TELEGRAM", "ROOM_ID"), text=message
                )
        except Exception as err:
            logger.error("err.args:")
            logger.error(err.args)
            logger.error(f"Unexpected {err=}, {type(err)=}")
            logger.error("\nString err:\n" + str(err))
            if retry_c > 4:
                logger.error("Telegram attempts exceeded. Message not sent.")
                break
            elif str(err) == "Unauthorized":
                logger.error("Invalid Telegram bot token, message not sent.")
                break
            elif str(err) == "Timed out":
                retry_c += 1
                logger.warning("Telegram timeout count: " + str(retry_c))

            elif str(err) == "Chat not found":
                logger.error("Invalid Telegram Chat ID, message not sent.")
                break
            elif str(err)[:35] == "[Errno 2] No such file or directory":
                logger.error("Telegram module couldn't find an image to send.")
                break
            elif str(err) == "Media_caption_too_long":
                logger.error(
                    "Telegram image caption length exceeds 1024 characters. Message not sent."
                )
                break
            else:
                logger.error("[X] Unknown Telegram error. Message not sent.")
                break
        else:
            logger.info("Telegram message successfully sent.")
    return sent
