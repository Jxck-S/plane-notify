"""socials/mastodon.py: Interface for posting status updates and media to Mastodon."""

from __future__ import annotations

import logging
from typing import Any

from mastodon import (
    Mastodon,
    MastodonError,
    MastodonGatewayTimeoutError,
    MastodonNetworkError,
)

logger = logging.getLogger(__name__)


def post(
    message: str,
    access_token: str,
    api_base_url: str,
    photo: Any = None,  # noqa: ANN401
    reply_to: str | int | None = None,
) -> Any:  # noqa: ANN401
    """
    Post a status update and optional media to Mastodon.

    :param message: The text content of the status.
    :param access_token: Mastodon API access token.
    :param api_base_url: Mastodon instance base URL.
    :param photo: File-like object or path to an image to upload.
    :param reply_to: ID of the status to reply to (optional).
    :return: The API response data if successful, None otherwise.
    """
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
                logger.exception("Mastodon attempts exceeded. Message not sent.")
                break
        except MastodonError as e:
            logger.exception("Mastodon error: %s", e)
            break
        except FileNotFoundError:
            logger.exception("Mastodon module couldn't find an image to send.")
            break
        except Exception as err:
            logger.exception("Unexpected Mastodon error: %s", err)
            break
        else:
            sent = True
            logger.info("Mastodon message successfully sent.")
            return post_result
    return sent
