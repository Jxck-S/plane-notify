import requests
from discord_webhook import DiscordWebhook


def send_discord_message(message, config, file_name=None, role_id=None):
    if role_id is not None:
        message += f" <@&{role_id}>"

    webhook = DiscordWebhook(
        url=config.get("DISCORD", "URL"),
        content=message[0:1999],
        username=config.get("DISCORD", "USERNAME"),
    )
    if file_name is not None:
        with open(file_name, "rb") as f:
            webhook.add_file(file=f.read(), filename=file_name)
    try:
        webhook.execute()
    except requests.exceptions.RequestException:
        pass
