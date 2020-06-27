# Authenticate to Twitter
def tweepysetup():
    #DOCU 
    #https://realpython.com/twitter-bot-python-tweepy/
    import tweepy
    auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
    auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")
    tweet_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return tweet_api