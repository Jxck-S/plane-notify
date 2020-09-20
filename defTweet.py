import configparser
config = configparser.ConfigParser()
config.read('config.ini')
import tweepy
def tweepysetup():
    auth = tweepy.OAuthHandler(config.get('TWITTER', 'CONSUMER_KEY'), config.get('TWITTER', 'CONSUMER_SECRET'))
    auth.set_access_token(config.get('TWITTER', 'ACCESS_TOKEN'), config.get('TWITTER', 'ACCESS_TOKEN_SECRET'))
    tweet_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return tweet_api