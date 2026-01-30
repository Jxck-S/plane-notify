import os
import traceback
import praw
from requests.exceptions import RequestException
from atproto import Client, models, exceptions as ATexceptions

import socials.discord as discord
import socials.telegram as telegram
import socials.mastodon as mastodon
import socials.meta as meta
import socials.nostr as nostr
from socials.x import XED
from socials.threads import Threads
from providers import Providers

class ReplyRefs:
    def __init__(self):
        self.mastodon = None
        self.x = None
        self.facebook = None
        self.bluesky = None
        self.nostr = None
        self.reddit = None

class NotificationManager:
    reddit_client = None

    @classmethod
    def init_sources(cls, main_config):
        # Initialize Reddit Client (Global)
        if cls.reddit_client is None and main_config.has_section('REDDIT') and main_config.getboolean("REDDIT", "ENABLE"):
            try:
                cls.reddit_client = praw.Reddit(
                    client_id=main_config.get("REDDIT", "CLIENT_ID"),
                    client_secret=main_config.get("REDDIT", "CLIENT_SECRET"),
                    password=main_config.get("REDDIT", "PASSWORD"),
                    user_agent=main_config.get("REDDIT", "USER_AGENT"),
                    username=main_config.get("REDDIT", "USERNAME"),
                )
            except Exception as e:
                discord.post(f"Failed to initialize Reddit client: {e}", main_config)

    def __init__(self, config, main_config):
        self.config = config
        self.main_config = main_config
        self.x_client = None
        self.reply_refs = ReplyRefs()
        self.exclusive_platforms = None

        # Initialize X Client
        if self.config.has_section('X') and self.config.getboolean('X', 'ENABLE'):
            try:
                x_info = self.config['X']
                self.x_client = XED(x_info['consumer_key'], x_info['consumer_secret'], x_info['access_token'], x_info['access_token_secret'])
            except Exception as e:
                 discord.post(f"Failed to initialize X client: {e}", self.main_config)

    def set_one_time_exclusive(self, platforms):
        self.exclusive_platforms = platforms

    def reset_state(self):
        self.reply_refs = ReplyRefs()
        self.exclusive_platforms = None

    def post_to_all(self, message, title, image_path, is_reply=False):
        """
        Post notification to all enabled platforms.
        If is_reply is True, attempts to reply to the thread started by the previous post.
        """
        # I will import apply_prefix from utils
        from utils import apply_prefix
        
        message_w_title = apply_prefix(title, message)
        
        # Helper to check if we should post to a platform
        def should_post(platform_name):
            if self.exclusive_platforms is not None:
                return platform_name.lower() in self.exclusive_platforms
            return True

        if not is_reply:
            self.reset_state()

        # Telegram
        if should_post(Providers.TELEGRAM) and self.config.has_section('TELEGRAM') and self.config.getboolean('TELEGRAM', 'ENABLE'):
            self._post_telegram(message_w_title, image_path)

        # Mastodon
        if should_post(Providers.MASTODON) and self.config.has_section('MASTODON') and self.config.getboolean('MASTODON', 'ENABLE'):
            self.reply_refs.mastodon = self._post_mastodon(message_w_title, image_path, is_reply)

        # Discord
        if should_post(Providers.DISCORD) and self.config.getboolean('DISCORD', 'ENABLE'):
            self._post_discord(message, title, image_path)

        # X (Twitter)
        if should_post(Providers.X) and self.config.getboolean('X', 'ENABLE') and self.x_client:
            self.reply_refs.x = self._post_x(message_w_title, image_path, is_reply, title)

        # Meta (FB & IG)
        if should_post(Providers.META) and self.config.has_option('META', 'ENABLE') and self.config.getboolean('META', 'ENABLE'):
             self.reply_refs.facebook = self._post_meta(message_w_title, image_path, is_reply)

        # BlueSky
        if should_post(Providers.BLUESKY) and self.config.getboolean('BLUESKY', 'ENABLE'):
            self.reply_refs.bluesky = self._post_bluesky(message_w_title, image_path, is_reply)

        # Nostr
        if should_post(Providers.NOSTR) and self.config.getboolean('NOSTR', 'ENABLE'):
             self.reply_refs.nostr = self._post_nostr(message_w_title, image_path, is_reply)

        # Threads
        if should_post(Providers.THREADS) and self.config.getboolean('THREADS', 'ENABLE'):
             self._post_threads(message_w_title, image_path)

        # Reddit
        if should_post(Providers.REDDIT) and self.config.getboolean('REDDIT', 'ENABLE'):
             self.reply_refs.reddit = self._post_reddit(message_w_title, image_path, is_reply)
        
    def reset_state(self):
        self.latest_reddit_submission = None
        self.exclusive_platforms = None

    def _post_telegram(self, message_w_title, image_path):
        try:
            with open(image_path, "rb") as photo:
                return telegram.post(message_w_title, self.config, photo)
        except RequestException as e:
             discord.post(f"Failed to post to Telegram : {e}", self.main_config)
             return None

    def _post_mastodon(self, message_w_title, image_path, is_reply):
        try:
             reply_id = self.reply_refs.mastodon if is_reply else None
             mastodon_post_info = mastodon.post(message_w_title, self.config, image_path if not is_reply else None, reply_id)
             return mastodon_post_info['id'] if mastodon_post_info else None
        except RequestException as e:
             discord.post(f"Failed to post to Mastodon : {e}", self.main_config)
             return None


    def _post_discord(self, message, title, image_path):
        # Role ID needed?
        role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') and self.config.get('DISCORD', 'ROLE_ID').strip() != "" else None
        
        return discord.post(message, self.config, role_id, image_path, username=title)

    def _post_x(self, message_w_title, image_path, is_reply, title=None):
        try:
             media_list = [(image_path, "Map Image")] if image_path else []
             
             in_reply_to_id = self.reply_refs.x if is_reply else None
             
             # x_client.post returns response, which likely contains id or we can get latest_post_id
             # Assuming x_client.post sets latest_post_id internally or we should check
             return self.x_client.post(message_w_title, media_list, in_reply_to_id=in_reply_to_id)
        except Exception as e:
             discord.post(f"Failed to post to X : {e}", self.main_config)
             return None

    def _post_meta(self, message_w_title, image_path, is_reply):
        # Facebook
        fb_id = None
        try:
            if is_reply and self.reply_refs.facebook:
                 # Comment on existing post
                 meta.post_fb_comment(self.config.get("META", "ACCESS_TOKEN"), self.reply_refs.facebook, message_w_title)
                 fb_id = self.reply_refs.facebook # Keep original ID
            else:
                 # New Post
                 fb_post_info = meta.post_fb(self.config.get("META", "FB_PAGE_ID"), image_path.replace(".png", ".jpg"), message_w_title, self.config.get("META", "ACCESS_TOKEN"))
                 fb_id = fb_post_info['id']
        except RequestException as e:
             discord.post(f"Failed to post to FaceBook : {e}", self.main_config)


        ig_id = None
        if not is_reply:
            try:
                # This requires HTTP_SERVE config from main_config to construct URL
                files_url = self.main_config.get('HTTP_SERVE', 'IMAGE_URL')
                full_filename = image_path.replace(".png", ".jpg") 
                
                image_url = f"{files_url}/{os.path.basename(full_filename)}"
                meta.post_to_instagram(self.config.get("META", "IG_USER_ID"), self.config.get("META", "ACCESS_TOKEN"), image_url, message_w_title)
                # IG ID logic?
            except Exception as e:
                 discord.post(f"Failed to post to Instagram : {e}", self.main_config)
        
        return fb_id

    def _post_bluesky(self, message_w_title, image_path, is_reply):
        try:
            ATclient = Client()
            ATclient.login(self.config.get("BLUESKY", "USERNAME"), self.config.get("BLUESKY", "PASSWORD"))            
            if is_reply and self.reply_refs.bluesky:
                 root_ref = self.reply_refs.bluesky['root']
                 parent_ref = self.reply_refs.bluesky['parent']
                 reply_ref = models.AppBskyFeedPost.ReplyRef(parent=parent_ref, root=root_ref)
                 post_ref = models.create_strong_ref(ATclient.send_post(text=message_w_title, reply_to=reply_ref))
                 self.reply_refs.bluesky['parent'] = post_ref
                 return self.reply_refs.bluesky
            else:
                with open(image_path.replace(".png", ".jpg"), 'rb') as f:
                    img_data = f.read()
                    first_post_ref = models.create_strong_ref(ATclient.send_image(text=message_w_title, image=img_data, image_alt="Map Image")) 
                    return {'root': first_post_ref, 'parent': first_post_ref}

        except Exception as e:
             discord.post(f"Failed to post to BlueSky : {e} {type(e)}", self.main_config)
             return None

    def _post_nostr(self, message_w_title, image_path, is_reply):
        try:
            if is_reply and self.reply_refs.nostr:
                 new_event = nostr.post(message_w_title, self.config.get("NOSTR", "PK"), reply_to=self.reply_refs.nostr)
                 return new_event
            else:
                 first_event = nostr.post_with_media(message_w_title, image_path, self.config.get("NOSTR", "PK"))
                 return first_event
        except Exception as e:
             discord.post(f"Failed to post to NOSTR : {e}", self.main_config)
             return None

    def _post_threads(self, message_w_title, image_path):
        try:
            access_token = self.config.get('THREADS', 'ACCESS_TOKEN')
            threads_client = Threads(access_token)
            files_url = self.main_config.get('HTTP_SERVE', 'IMAGE_URL')
            if image_path:
                full_filename = image_path 
                image_url = f"{files_url}/{os.path.basename(full_filename)}"
                container_id = threads_client.create_image_container(image_url, text=message_w_title)
                threads_client.publish_container(container_id)
            else:

                 pass
            return None
        except Exception as e:
             discord.post(f"Failed to post to Threads : {type(e)}, {e}", self.main_config)
             return None

    def _post_reddit(self, message_w_title, image_path, is_reply):
        if self.reddit_client:
            try:
                new_submission = None
                if is_reply and self.reply_refs.reddit:
                    # Reply to existing submission
                    self.reply_refs.reddit.reply(message_w_title)
                    new_submission = self.reply_refs.reddit # Keep same submission as ref
                else:
                    new_submission = self.reddit_client.subreddit(self.config.get("REDDIT", "SUBREDDIT")).submit_image(message_w_title, image_path)
                
                return new_submission
            except Exception as e:
                 discord.post(f"Failed to post to Reddit : {type(e)}, {e}", self.main_config)
                 return self.reply_refs.reddit
        return None
