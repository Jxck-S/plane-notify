"""socials/discord.py: Interface for sending messages and files to Discord via webhooks."""

import logging

import requests
from discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)


def post(message, webhook_url, role_id=None, *file_names, username=None) -> None:
    """Send a message and optional files to a Discord channel via webhook.

    :param message: The text content of the message.
    :param webhook_url: Discord webhook URL.
    :param role_id: Discord role ID to mention (optional).
    :param file_names: Path(s) to file(s) to upload.
    :param username: Override the webhook's default username.
    """
    if role_id:
        message += f" <@&{role_id}>"
    webhook = DiscordWebhook(
        url=webhook_url, content=message[0:1999], username=username
    )

    if file_names:
        for file_name in file_names:
            try:
                with open(file_name, "rb") as f:
                    webhook.add_file(file=f.read(), filename=file_name)
            except Exception as e:
                logger.exception(
                    f"Failed to read file {file_name} for Discord message: {e}"
                )

    try:
        webhook.execute()
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to send Discord message: %s", e)
    except Exception as e:
        logger.exception("Unexpected error sending Discord message: %s", e)
