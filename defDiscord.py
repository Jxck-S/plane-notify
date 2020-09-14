
def sendDis(message, map_file_name, conf_file):
    from discord_webhook import DiscordWebhook
    import configparser
    config = configparser.ConfigParser()
    config.read(conf_file)
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message, username=config.get('DISCORD', 'USERNAME'))

    with open(map_file_name, "rb") as f:
        webhook.add_file(file=f.read(), filename='map.png')
    response = webhook.execute()