import requests

class Threads:
    base_url = 'https://graph.threads.net/v1.0/'
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.debug = False

    def toggle_debug(self, debug: bool):
        self.debug = debug

    def create_image_container(self, image_url, user_id='me', text=None, is_carousel_item=False):
        """
        Creates a media container with an image to be posted on Threads.

        :param image_url: The URL of the image to be posted.
        :param text: Optional text content to be posted.
        :return: The response from the API call.
        """
        params = {
            'media_type': 'IMAGE',
            'access_token': self.access_token,
            'image_url': image_url,
            'is_carousel_item': is_carousel_item
        }
        if text:
            params['text'] = text
        create_container_response = requests.post(
            f'{Threads.base_url}{user_id}/threads',
            params=params
        )
        create_container_response.raise_for_status()
        if self.debug:
            print("create_container_response", create_container_response.status_code, create_container_response.text)
        return create_container_response.json()['id']

    def create_video_container(self, video_url, user_id='me', text=None, is_carousel_item=False):
        """
        Creates a media container with a video to be posted on Threads.

        :param video_url: The URL of the video to be posted.
        :param text: Optional text content to be posted.
        :return: The response from the API call.
        """
        params = {
            'media_type': 'VIDEO',
            'access_token': self.access_token,
            'video_url': video_url,
            'is_carousel_item': is_carousel_item
        }
        create_container_response = requests.post(
            f'{Threads.base_url}{user_id}/threads',
            params=params
        )
        create_container_response.raise_for_status()
        if self.debug:
            print("create_container_response", create_container_response.status_code, create_container_response.text)
        return create_container_response.json()['id']

    def create_text_container(self, text, user_id='me', is_carousel_item=False):
        """
        Creates a media container with text content to be posted on Threads.

        :param text: The text content to be posted.
        :return: The response from the API call.
        """
        params = {
            'media_type': 'TEXT',
            'access_token': self.access_token,
            'text': text,
            'is_carousel_item': is_carousel_item
        }
        create_container_response = requests.post(
            f'{Threads.base_url}{user_id}/threads',
            params=params
        )
        create_container_response.raise_for_status()
        if self.debug:
            print("create_container_response", create_container_response.status_code, create_container_response.text)
        return create_container_response.json()['id']




    def publish_container(self, threads_media_container_id, user_id='me'):
        """
        Publishes a container (post) that was created using the `create_container` method.

        :param threads_media_container_id: The container ID obtained from the create_container method.
        :return: The response from the API call.
        """
        params = {
            'access_token': self.access_token,
            'creation_id': threads_media_container_id,
        }

        publish_container_response = requests.post(
            f'{Threads.base_url}{user_id}/threads_publish',
            params=params
        )
        if self.debug:
            print("publish_container_response", publish_container_response.status_code ,publish_container_response.json())
        return publish_container_response


    def create_carousel_container(self, children, user_id='me', text=None):
        """
        Creates a carousel container with images or videos.

        :param children: A list of container IDs (up to 20) for images/videos to be included in the carousel.
        :param text: Optional text associated with the carousel post.
        :return: The response from the API call.
        """
        if len(children) < 2 or len(children) > 20:
            raise ValueError("Carousel must have at least 2 and up to 20 total images or videos.")

        params = {
            'media_type': 'CAROUSEL',
            'children': ','.join(children),  # Convert list of children container IDs to a comma-separated string
            'access_token': self.access_token
        }

        # Include the text if provided
        if text:
            params['text'] = text

        create_carousel_response = requests.post(
            f'{Threads.base_url}{user_id}/threads',
            params=params
        )
        if self.debug:
            print("create_carousel_response", create_carousel_response.status_code ,create_carousel_response.json())
        return create_carousel_response.json()['id']


    def reply_to_post(self, text, reply_to_id):
        """
        Replies to a specific reply under the root post.

        :param text: The reply text content.
        :param reply_to_id: The ID of the specific post/reply being replied to.
        :return: The response from the API call.
        """
        params = {
            'media_type': "TEXT",
            'text': text,
            'reply_to_id': reply_to_id,
            'access_token': self.access_token
        }

        reply_response = requests.post(
            f'{Threads.base_url}me/threads',
            params=params
        )

        return reply_response






