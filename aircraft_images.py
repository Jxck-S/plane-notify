import json, os
import requests
from io import BytesIO
from PIL import Image
AIRCRAFT_SILS_DIR = "aircraft_sils"
TIMEOUT_SECS = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def get_planespotters_net_aircraft_photo(reg):
    try:
        print("Getting planespotters pic")
        headers={"User-Agent": USER_AGENT}
        rsp = requests.get(f"https://api.planespotters.net/pub/photos/reg/{reg}", headers=headers, timeout=TIMEOUT_SECS)
        
        if rsp.status_code != 200:
            print(f"Planespotters API returned status code {rsp.status_code} for {reg}")
            return None
            
        if not rsp.text.strip():
            print(f"Planespotters API returned empty response for {reg}")
            return None
            
        ps_reg_photo_info = json.loads(rsp.text)
        print(ps_reg_photo_info)
        if "photos" in ps_reg_photo_info and len(ps_reg_photo_info['photos']) > 0:
            photo = ps_reg_photo_info['photos'][0]
            url = photo['thumbnail']['src']
            credit = photo['photographer']
            data = {
                'image_url': url,
                'credit': credit,
            }
            return data
        else:
            return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response from Planespotters API for {reg}: {e}")
        print(f"Response content: {rsp.text[:200]}...")  # Show first 200 chars
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error when fetching from Planespotters API for {reg}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_planespotters_net_aircraft_photo for {reg}: {e}")
        return None
def get_github_aircraft_photo(reg):
    try:
        print("Getting Github List")
        rsp = requests.get("https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/photo-list.json", timeout=TIMEOUT_SECS, headers={"User-Agent": USER_AGENT})
        
        if rsp.status_code != 200:
            print(f"GitHub photo list returned status code {rsp.status_code} for {reg}")
            return None
            
        if not rsp.text.strip():
            print(f"GitHub photo list returned empty response for {reg}")
            return None
            
        photo_list = json.loads(rsp.text)
        if reg in photo_list.keys():
            photo_name = photo_list[reg]['photo']
            url = f"https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/images/{photo_name}"
            credit = photo_list[reg]['photographer']
            return {"image_url": url, "credit": credit}
        else:
            return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response from GitHub photo list for {reg}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error when fetching GitHub photo list for {reg}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_github_aircraft_photo for {reg}: {e}")
        return None
def get_aircraft_sil(type_code):
    sil_path =  os.path.join(AIRCRAFT_SILS_DIR, f'{type_code.upper()}.png')
    print(sil_path)
    if type_code and os.path.exists(sil_path):
        print(sil_path)

        return sil_path
    else:
        return None


def get_aircraft_image_url(reg):
    photo = None
    if photo:= get_github_aircraft_photo(reg):
        pass
    elif photo := get_planespotters_net_aircraft_photo(reg):
        pass

    return photo

def get_image_from_url(photo):
    try:
        url = photo['image_url']
        response = requests.get(url, timeout=TIMEOUT_SECS, headers={"User-Agent": USER_AGENT})

        if response.status_code == 200:
            # Read image data from the response content
            image_data = BytesIO(response.content)
            return image_data
        else:
            print(f"Failed to fetch image. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error when fetching image from {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_image_from_url for {url}: {e}")
        return None

#print(get_aircraft_image_url("N628TS"))
# print(get_aircraft_image_url("N2N"))

#print(get_aircraft_image_url("N327JT"))
#print(get_planespotters_net_aircraft_photo("N327JT"))