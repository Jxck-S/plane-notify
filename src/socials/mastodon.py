import logging

logger = logging.getLogger(__name__)


def post(message, config, photo=None, reply_to=None):
    from mastodon import Mastodon

    sent = False
    retry_c = 0
    while sent == False:
        try:
            bot = Mastodon(
                access_token=config.get("MASTODON", "ACCESS_TOKEN"),
                api_base_url=config.get("MASTODON", "APP_URL"),
            )
            if photo:
                media_id = bot.media_post(photo, mime_type="image/jpeg")
            sent = bot.status_post(
                message, reply_to, (media_id if photo else None), False, "Public"
            )
        except Exception as err:
            logger.error("err.args:")
            logger.error(err.args)
            logger.error(f"Unexpected {err=}, {type(err)=}")
            logger.error("\nString err:\n" + str(err))
            if retry_c > 4:
                logger.error("Mastodon attempts exceeded. Message not sent.")
                break
            elif str(err) == "Unauthorized":
                logger.error("Invalid Mastodon bot token, message not sent.")
                break
            elif str(err) == "Timed out":
                retry_c += 1
                logger.warning("Mastodon timeout count: " + str(retry_c))
            elif str(err)[:35] == "[Errno 2] No such file or directory":
                logger.error("Mastodon module couldn't find an image to send.")
                break
            elif str(err) == "Media_caption_too_long":
                logger.error(
                    "Mastodon image caption lenght exceeds 1024 characters. Message not send."
                )
                break
            else:
                logger.error("Unknown error. Message not sent.")
                break
        else:
            logger.info("Mastodon message successfully sent.")
    return sent
