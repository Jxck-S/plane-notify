def sendDis(message, config, image_name = None):
    import requests
    from discord_webhook import DiscordWebhook
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message[0:1999], username=config.get('DISCORD', 'USERNAME'))
    if image_name != None:
        with open(image_name, "rb") as f:
            webhook.add_file(file=f.read(), filename='map.png')
    try:
        webhook.execute()
    except requests.Exceptions:
        pass