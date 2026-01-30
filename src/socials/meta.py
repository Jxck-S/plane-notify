import requests
import json

API_VERSION = "v20.0"
def raise_details(resp):
    try: 
        resp.raise_for_status()
    except Exception as e:
        if resp.status_code == 500:
            #Facebook 500 is usually bad auth but they don't say. Zuck makes me angry 
            raise requests.exceptions.HTTPError(f"{e}, Likely bad Meta auth or permissions.")
        else:
            raise(e)
    
def post_fb(page_id, file_path, message, access_token):
    """Posts to Facebook with Image"""
    import os
    file_name = os.path.basename(file_path) 
    files= {'image':(file_name, open(file_path, 'rb'), "multipart/form-data")}
    url = f"https://graph.facebook.com/{API_VERSION}/{page_id}/photos?message={message}&access_token={access_token}"
    resp = requests.post(url, files=files)
    raise_details(resp)
    print("Facebook Post Response: ", resp.json())
    return resp.json()

def post_fb_text(page_id, message, access_token):
    """Posts text-only to Facebook"""
    url = f"https://graph.facebook.com/{API_VERSION}/{page_id}/feed?message={message}&access_token={access_token}"
    resp = requests.post(url)
    raise_details(resp)
    print("Facebook Text Post Response: ", resp.json())
    return resp.json()

def post_fb_comment(access_token, post_id, comment):
    """Comment on Facebook post"""
    comment_url = f'https://graph.facebook.com/{API_VERSION}/{post_id}/comments?message={comment}&access_token={access_token}'
    comment_resp = requests.post(comment_url)
    comment_resp.raise_for_status()
    
    return comment_resp

def get_fb_post_image_link(post_id, access_token):
    """Returns Highest Resolution image link of a Facebook Post by FBID"""
    url = f"https://graph.facebook.com/{API_VERSION}/{post_id}?fields=images&access_token={access_token}"
    resp = requests.get(url)
    raise_details(resp)
    image_url = resp.json()['images'][0]['source']
    print("Highest Resoulution Image URL for FBID", post_id, "is", image_url)
    return image_url

def post_to_instagram(ig_user_id, access_token, image_url, caption):
    """Posts to Instagram"""
    post_url = f'https://graph.facebook.com/{API_VERSION}/{ig_user_id}/media'
    payload = {
    'caption': caption,
    'access_token': access_token,
    'image_url': image_url
    }
    resp = requests.post(post_url, data=payload)
    raise_details(resp)
    print("IG Media Response:", resp.json())
    result = json.loads(resp.text)
    if 'id' in result:
        creation_id = result['id']
        second_url = f'https://graph.facebook.com/{API_VERSION}/{ig_user_id}/media_publish'
        second_payload = {
        'creation_id': creation_id,
        'access_token':access_token
        }
        resp = requests.post(second_url, data=second_payload)
        raise_details(resp)
        print('Posted to Instagram', caption, "IG response:", resp.json())
    else:
        print('Could not post to Instagram: ', resp.json())
    return result
def post_both(fb_page_id, ig_user_id, file_path, message, access_token):
    """Posts to Facebook and Instagram"""
    if file_path:
        fb_post_info = post_fb(fb_page_id, file_path, message, access_token)
        fb_image_link = get_fb_post_image_link(fb_post_info['id'], access_token)
        ig_post_info = post_to_instagram(ig_user_id, access_token, fb_image_link, message)
        return fb_post_info, ig_post_info
    else:
         fb_post_info = post_fb_text(fb_page_id, message, access_token)
         return fb_post_info, None

def post_to_meta_both_v(fb_page_id, ig_user_id, file_path, access_token, facebook_caption, insta_caption):
    """Posts to Facebook and Instagram with different captions"""
    fb_post_info = post_fb(fb_page_id, file_path, facebook_caption, access_token)
    fb_image_link = get_fb_post_image_link(fb_post_info['id'], access_token)
    ig_post_info = post_to_instagram(ig_user_id, access_token, fb_image_link, insta_caption)
    return fb_post_info, ig_post_info
