import logging
import requests
from discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)


def post(message, webhook_url, role_id=None, *file_names, username=None):
    if role_id is not None:
        message += f" <@&{role_id}>"
    webhook = DiscordWebhook(
        url=webhook_url, content=message[0:1999], username=username
    )

    if file_names:
        for file_name in file_names:
            if file_name:
                with open(file_name, "rb") as f:
                    webhook.add_file(file=f.read(), filename=file_name)
    try:
        webhook.execute()
    except requests.exceptions.RequestException:
        pass
