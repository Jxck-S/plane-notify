from discord_webhook import DiscordWebhook
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
def sendDis(message):
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message, username="plane-notify")

    with open("map.png", "rb") as f:
        webhook.add_file(file=f.read(), filename='map.png')
    response = webhook.execute()