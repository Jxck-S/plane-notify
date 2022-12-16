import requests
import json
def post_fb(page_id, file_path, message, access_token):
    """Posts to Facebook with Image"""
    import os
    file_name = os.path.basename(file_path) 
    files= {'image':(file_name, open(file_path, 'rb'), "multipart/form-data")}
    url = f"https://graph.facebook.com/{page_id}/photos?message={message}&access_token={access_token}"
    resp = requests.post(url, files=files)
    resp.raise_for_status()
    print("Facebook Post Response: ", resp.json())
    return resp.json()

def get_fb_post_image_link(post_id, access_token):
    """Returns Highest Resolution image link of a Facebook Post by FBID"""
    url = f"https://graph.facebook.com/{post_id}?fields=images&access_token={access_token}"
    resp = requests.get(url)
    resp.raise_for_status()
    image_url = resp.json()['images'][0]['source']
    print("Highest Resoulution Image URL for FBID", post_id, "is", image_url)
    return image_url

def post_to_instagram(ig_user_id, access_token, image_url, caption):
    """Posts to Instagram"""
    post_url = f'https://graph.facebook.com/v13.0/{ig_user_id}/media'
    payload = {
    'caption': caption,
    'access_token': access_token,
    'image_url': image_url
    }
    resp = requests.post(post_url, data=payload)
    resp.raise_for_status()
    print("IG Media Response:", resp.json())
    result = json.loads(resp.text)
    if 'id' in result:
        creation_id = result['id']
        second_url = f'https://graph.facebook.com/v13.0/{ig_user_id}/media_publish'
        second_payload = {
        'creation_id': creation_id,
        'access_token':access_token
        }
        resp = requests.post(second_url, data=second_payload)
        resp.raise_for_status()
        print('Posted to Instagram', caption, "IG response:", resp.json())
    else:
        print('Could not post to Instagram: ', resp.json())
def post_to_meta_both(fb_page_id, ig_user_id, file_path, message, access_token):
    """Posts to Facebook and Instagram"""
    post_info = post_fb(fb_page_id, file_path, message, access_token)
    fb_image_link = get_fb_post_image_link(post_info['id'], access_token)
    post_to_instagram(ig_user_id, access_token, fb_image_link, message)
