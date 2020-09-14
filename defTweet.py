# Authenticate to Twitter

def tweepysetup(conf_file):
    import configparser
    config = configparser.ConfigParser()
    config.read(conf_file)
    import tweepy
    #DOCU
    #https://realpython.com/twitter-bot-python-tweepy/
    auth = tweepy.OAuthHandler(config.get('TWITTER', 'CONSUMER_KEY'), config.get('TWITTER', 'CONSUMER_SECRET'))
    auth.set_access_token(config.get('TWITTER', 'ACCESS_TOKEN'), config.get('TWITTER', 'ACCESS_TOKEN_SECRET'))
    tweet_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return tweet_api