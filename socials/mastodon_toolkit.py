def sendMastodon(photo, message, config):
    from mastodon import Mastodon
    sent = False
    retry_c = 0
    while sent == False:
        try:
            bot  = Mastodon(
                access_token=config.get('MASTODON','ACCESS_TOKEN'),
                api_base_url=config.get('MASTODON','APP_URL')
            )
            mediaid = bot.media_post(photo, mime_type="image/jpeg")
            sent =  bot.status_post(message,None,mediaid,False, "Public")
        except Exception as err:
            print('err.args:')
            print(err.args)
            print(f"Unexpected {err=}, {type(err)=}")
            print("\nString err:\n"+str(err))
            if retry_c > 4:
                print('Mastodon attempts exceeded. Message not sent.')
                break
            elif str(err) == 'Unauthorized':
                print('Invalid Mastodon bot token, message not sent.')
                break
            elif str(err) == 'Timed out':
                retry_c += 1
                print('Mastodon timeout count: '+str(retry_c))
                pass
            elif str(err)[:35] == '[Errno 2] No such file or directory':
                print('Mastodon module couldn\'t find an image to send.')
                break
            elif str(err) == 'Media_caption_too_long':
                print('Mastodon image caption lenght exceeds 1024 characters. Message not send.')
                break
            else:
                print('[X] Unknown error. Message not sent.')
                break
        else:
            print("Mastodon message successfully sent.")
    return sent
