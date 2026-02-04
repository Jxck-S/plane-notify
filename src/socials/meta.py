"""socials/meta.py: Interface for posting to Meta platforms (Facebook and Instagram)."""

from __future__ import annotations

import json
import logging

import requests
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

API_VERSION = "v20.0"


def raise_details(resp: requests.Response) -> None:
    """
    Handle HTTP response errors with descriptive messages.

    :param resp: The requests response object to check.
    """
    try:
        resp.raise_for_status()
    except Exception as e:
        if resp.status_code == 500:
            # Facebook 500 is usually bad auth but they don't say. Zuck makes me angry
            msg = f"{e}, Likely bad Meta auth or permissions."
            raise requests.exceptions.HTTPError(msg) from e
        raise


def post_fb(page_id: str, file_path: str, message: str, access_token: str) -> Any:  # noqa: ANN401
    """
    Post an image and message to a Facebook page.

    :param page_id: The Facebook Page ID to post to.
    :param file_path: Path to the image file to upload.
    :param message: The text caption for the post.
    :param access_token: Meta Page Access Token.
    :return: The JSON response from the Facebook API.
    """
    file_name = Path(file_path).name
    files = {"image": (file_name, Path(file_path).open("rb"), "multipart/form-data")}
    url = f"https://graph.facebook.com/{API_VERSION}/{page_id}/photos?message={message}&access_token={access_token}"
    resp = requests.post(url, files=files)
    raise_details(resp)
    logger.debug("Facebook Post Response: %s", resp.json())
    return resp.json()


def post_fb_text(page_id: str, message: str, access_token: str) -> Any:  # noqa: ANN401
    """
    Post a text-only status update to a Facebook page.

    :param page_id: The Facebook Page ID to post to.
    :param message: The text content of the post.
    :param access_token: Meta Page Access Token.
    :return: The JSON response from the Facebook API.
    """
    url = f"https://graph.facebook.com/{API_VERSION}/{page_id}/feed?message={message}&access_token={access_token}"
    resp = requests.post(url)
    raise_details(resp)
    logger.debug("Facebook Text Post Response: %s", resp.json())
    return resp.json()


def post_fb_comment(access_token: str, post_id: str, comment: str) -> requests.Response:
    """
    Post a comment on an existing Facebook post.

    :param access_token: Meta Access Token.
    :param post_id: The ID of the post to comment on.
    :param comment: The text of the comment.
    :return: The requests response object.
    """
    comment_url = f"https://graph.facebook.com/{API_VERSION}/{post_id}/comments?message={comment}&access_token={access_token}"
    comment_resp = requests.post(comment_url)
    comment_resp.raise_for_status()

    return comment_resp


def get_fb_post_image_link(post_id: str, access_token: str) -> str:
    """
    Retrieve the highest resolution image link of a Facebook post by its ID.

    :param post_id: The Facebook post ID.
    :param access_token: Meta Access Token.
    :return: The URL of the highest resolution image.
    """
    url = f"https://graph.facebook.com/{API_VERSION}/{post_id}?fields=images&access_token={access_token}"
    resp = requests.get(url)
    raise_details(resp)
    image_url = resp.json()["images"][0]["source"]
    logger.debug("Highest Resoulution Image URL for FBID %s is %s", post_id, image_url)
    return image_url


def post_to_instagram(
    ig_user_id: str, access_token: str, image_url: str, caption: str
) -> Any:  # noqa: ANN401
    """
    Post an image to Instagram.

    :param ig_user_id: The Instagram User ID.
    :param access_token: Meta Access Token.
    :param image_url: Publicly accessible URL of the image to post.
    :param caption: The caption for the Instagram post.
    :return: The JSON result from the Instagram API.
    """
    post_url = f"https://graph.facebook.com/{API_VERSION}/{ig_user_id}/media"
    payload = {"caption": caption, "access_token": access_token, "image_url": image_url}
    resp = requests.post(post_url, data=payload)
    raise_details(resp)
    logger.debug("IG Media Response: %s", resp.json())
    result = json.loads(resp.text)
    if "id" in result:
        creation_id = result["id"]
        second_url = (
            f"https://graph.facebook.com/{API_VERSION}/{ig_user_id}/media_publish"
        )
        second_payload = {"creation_id": creation_id, "access_token": access_token}
        resp = requests.post(second_url, data=second_payload)
        raise_details(resp)
        logger.info("Posted to Instagram %s IG response: %s", caption, resp.json())
    else:
        logger.error("Could not post to Instagram: %s", resp.json())
    return result


def post_both(
    fb_page_id: str,
    ig_user_id: str,
    file_path: str | None,
    message: str,
    access_token: str,
) -> tuple[Any, Any]:
    """
    Post a message (and optional image) to both Facebook and Instagram.

    :param fb_page_id: Facebook Page ID.
    :param ig_user_id: Instagram User ID.
    :param file_path: Path to the image file to upload (optional).
    :param message: The text caption for the posts.
    :param access_token: Meta Access Token.
    :return: A tuple of (fb_response, ig_response).
    """
    if file_path:
        fb_post_info = post_fb(fb_page_id, file_path, message, access_token)
        fb_image_link = get_fb_post_image_link(fb_post_info["id"], access_token)
        ig_post_info = post_to_instagram(
            ig_user_id, access_token, fb_image_link, message
        )
        return fb_post_info, ig_post_info
    fb_post_info = post_fb_text(fb_page_id, message, access_token)
    return fb_post_info, None


def post_to_meta_both_v(
    fb_page_id: str,
    ig_user_id: str,
    file_path: str,
    access_token: str,
    facebook_caption: str,
    insta_caption: str,
) -> tuple[Any, Any]:
    """
    Post an image to Facebook and Instagram with different captions for each.

    :param fb_page_id: Facebook Page ID.
    :param ig_user_id: Instagram User ID.
    :param file_path: Path to the image file.
    :param access_token: Meta Access Token.
    :param facebook_caption: Caption for the Facebook post.
    :param insta_caption: Caption for the Instagram post.
    :return: A tuple of (fb_response, ig_response).
    """
    fb_post_info = post_fb(fb_page_id, file_path, facebook_caption, access_token)
    fb_image_link = get_fb_post_image_link(fb_post_info["id"], access_token)
    ig_post_info = post_to_instagram(
        ig_user_id, access_token, fb_image_link, insta_caption
    )
    return fb_post_info, ig_post_info
