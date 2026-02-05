"""socials/x.py: Interface for posting messages and media to X (formerly Twitter)."""

from __future__ import annotations

import tweepy


class XED:
    """X (Twitter) client for posting status updates and media."""

    def __init__(
        self,
        api_key: str,
        api_key_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        """Initialize X client with API credentials."""
        self._api_key = api_key
        self._api_key_secret = api_key_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret

    def post(
        self,
        message: str,
        media_list: list[tuple[bytes, str]] | None = None,
        in_reply_to_id: str | None = None,
    ) -> str:
        """
        Post a message to X with optional media and reply tagging.

        :param message: The text content of the post.
        :param media_list: List of (image_data, alt_text) tuples for media uploads.
        :param in_reply_to_id: Optional ID of a tweet to reply to.
        :return: The ID of the created tweet.
        """
        # V1 API For the Media Upload
        media_ids = []
        if media_list:
            twitter_app_auth = tweepy.OAuthHandler(self._api_key, self._api_key_secret)
            twitter_app_auth.set_access_token(
                self._access_token, self._access_token_secret
            )
            v1_tweet_api = tweepy.API(twitter_app_auth, wait_on_rate_limit=True)
            for media in media_list:
                img = media[0]
                alt_text = media[1]
                twitter_media_obj = v1_tweet_api.media_upload(img)
                v1_tweet_api.create_media_metadata(
                    media_id=twitter_media_obj.media_id, alt_text=alt_text
                )
                media_ids.append(twitter_media_obj.media_id)
        # 2 API for the Post
        v2_tweet_api = tweepy.Client(
            consumer_key=self._api_key,
            consumer_secret=self._api_key_secret,
            access_token=self._access_token,
            access_token_secret=self._access_token_secret,
        )
        if not media_ids:
            media_ids = None
        tweet_rsp = v2_tweet_api.create_tweet(
            text=message, media_ids=media_ids, in_reply_to_tweet_id=in_reply_to_id
        )
        return tweet_rsp.data["id"]
