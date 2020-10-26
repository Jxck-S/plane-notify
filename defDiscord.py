
def sendDis(message, map_file_name, config):
    from discord_webhook import DiscordWebhook
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message, username=config.get('DISCORD', 'USERNAME'))

    with open(map_file_name, "rb") as f:
        webhook.add_file(file=f.read(), filename='map.png')
    response = webhook.execute()