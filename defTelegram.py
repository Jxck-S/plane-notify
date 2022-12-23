def sendTeleg(photo, message, config):
    import telegram
    sent = False
    retry_c = 0
    while sent == False:
        try:
            bot = telegram.Bot(token=config.get('TELEGRAM', 'BOT_TOKEN'), request=telegram.utils.request.Request(connect_timeout=20, read_timeout=20))
            sent = bot.send_photo(chat_id=config.get('TELEGRAM', 'ROOM_ID'), photo=photo, caption=message, parse_mode=telegram.ParseMode.MARKDOWN, timeout=20)
        except Exception as err:
            print('err.args:')
            print(err.args)
            print(f"Unexpected {err=}, {type(err)=}")
            print("\nString err:\n"+str(err))
            if retry_c > 4:
                print('Telegram attempts exceeded. Message not sent.')
                break
            elif str(err) == 'Unauthorized':
                print('Invalid Telegram bot token, message not sent.')
                break
            elif str(err) == 'Timed out':
                retry_c += 1
                print('Telegram timeout count: '+str(retry_c))
                pass
            elif str(err) == 'Chat not found':
                print('Invalid Telegram Chat ID, message not sent.')
                break
            elif str(err)[:35] == '[Errno 2] No such file or directory':
                print('Telegram module couldn\'t find an image to send.')
                break
            elif str(err) == 'Media_caption_too_long':
                print('Telegram image caption length exceeds 1024 characters. Message not send.')
                break
            else:
                print('[X] Unknown Telegram error. Message not sent.')
                break
        else:
            print("Telegram message successfully sent.")
    return sent
