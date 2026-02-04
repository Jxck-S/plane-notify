import logging

from mastodon import (
    Mastodon,
    MastodonError,
    MastodonGatewayTimeoutError,
    MastodonNetworkError,
)

logger = logging.getLogger(__name__)


def post(message, access_token, api_base_url, photo=None, reply_to=None):
    sent = False
    retry_c = 0
    while not sent:
        try:
            bot = Mastodon(access_token=access_token, api_base_url=api_base_url)
            if photo:
                # Reset cursor for retries
                if hasattr(photo, "seek"):
                    photo.seek(0)
                media_id = bot.media_post(photo, description=message)
                post_result = bot.status_post(
                    message, media_ids=[media_id], in_reply_to_id=reply_to
                )
            else:
                post_result = bot.status_post(message, in_reply_to_id=reply_to)
        except (MastodonNetworkError, MastodonGatewayTimeoutError):
            retry_c += 1
            logger.warning("Mastodon timeout count: %s", retry_c)
            if retry_c > 4:
                logger.error("Mastodon attempts exceeded. Message not sent.")
                break
        except MastodonError as e:
            logger.error("Mastodon error: %s", e)
            break
        except FileNotFoundError:
            logger.error("Mastodon module couldn't find an image to send.")
            break
        except Exception as err:
            logger.error("Unexpected Mastodon error: %s", err)
            break
        else:
            sent = True
            logger.info("Mastodon message successfully sent.")
            return post_result
    return sent
