def sendDis(message, config, role_id = None, *file_names):
    import requests
    from discord_webhook import DiscordWebhook
    if role_id != None:
        message += f" <@&{role_id}>"
    webhook = DiscordWebhook(url=config.get('DISCORD', 'URL'), content=message[0:1999], username=config.get('DISCORD', 'USERNAME'))
    
    if file_names != []:
        for file_name in file_names:
            with open(file_name, "rb") as f:
                webhook.add_file(file=f.read(), filename=file_name)
    try:
        webhook.execute()
    except requests.exceptions.RequestException:
        pass