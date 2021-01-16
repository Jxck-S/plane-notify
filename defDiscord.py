
def sendDis(message, config, image_name = None):
    from discord_webhook import DiscordWebhook
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message, username=config.get('DISCORD', 'USERNAME'))

    if image_name != None:
        with open(image_name, "rb") as f:
            webhook.add_file(file=f.read(), filename='map.png')
    webhook.execute()