class XED:
    def __init__(self, api_key, api_key_secret, access_token, access_token_secret):
        self._api_key = api_key
        self._api_key_seret = api_key_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret
        self.latest_post_id = None
    def post(self, message, reply_message=None, media_list=None, in_reply_to_id=None):        
        print("Posting to X")
        import tweepy
        #V1 API For the Media Upload
        media_ids = []
        if media_list:
            twitter_app_auth = tweepy.OAuthHandler(self._api_key, self._api_key_seret)
            twitter_app_auth.set_access_token(self._access_token, self._access_token_secret)
            v1_tweet_api = tweepy.API(twitter_app_auth, wait_on_rate_limit=True)
            for media in media_list:
                img = media[0]
                alt_text = media[1]
                twitter_media_obj = v1_tweet_api.media_upload(img)
                v1_tweet_api.create_media_metadata(media_id= twitter_media_obj.media_id, alt_text=alt_text)
                media_ids.append(twitter_media_obj.media_id)
        #2 API for the Post
        v2_tweet_api = tweepy.Client(
            consumer_key=self._api_key,
            consumer_secret=self._api_key_seret,
            access_token=self._access_token,
            access_token_secret=self._access_token_secret
        )
        if not media_ids:
            media_ids = None
        tweet_rsp = v2_tweet_api.create_tweet(text=message, media_ids=media_ids, in_reply_to_tweet_id=in_reply_to_id)
        tweet_id = tweet_rsp.data['id']
        self.latest_post_id = tweet_id
        if reply_message:
            rply_rsp = v2_tweet_api.create_tweet(text=reply_message, in_reply_to_tweet_id=tweet_id)
            rply_id = rply_rsp.data['id']
            self.latest_post_id = rply_id