from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

import time
import os
import platform
import requests
import json
import re

from datetime import datetime, timedelta

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.headless = True
CHROME_OPTIONS.add_argument("window-size=800,800")
CHROME_OPTIONS.add_argument("ignore-certificate-errors")
CHROME_OPTIONS.add_argument("--enable-logging --v=1")

BROWSER = webdriver.Chrome(ChromeDriverManager().install(), options=CHROME_OPTIONS)
BROWSER.set_page_load_timeout(80)

REMOVE_ID_ELEMENTS = [
    "show_trace",
    "credits",
    "infoblock_close",
    "selected_photo_link",
    "history_collapse",
]

if platform.system() == "Linux" and os.getuid() == 0:
    CHROME_OPTIONS.add_argument(
        "--no-sandbox"
    )  # required when running as root user. otherwise you would get no sandbox errors.


def get_adsbx_screenshot(
    file_path, url_params, enable_labels=False, enable_track_labels=False
):
    url = f"https://globe.adsbexchange.com/?{url_params}"
    BROWSER.get(url)

    for element in REMOVE_ID_ELEMENTS:
        try:
            element = BROWSER.find_element_by_id(element)
            BROWSER.execute_script(
                """
                var element = arguments[0];    
                element.parentNode.removeChild(element); 
                """,
                element,
            )
        except:
            print("issue removing", element, "from map")

    # Remove watermark on data
    try:
        BROWSER.execute_script(
            "document.getElementById('selected_infoblock').className = 'none';"
        )
    except:
        print("Couldn't remove watermark from map")

    # Disable slidebar
    try:
        BROWSER.execute_script("$('#infoblock-container').css('overflow', 'hidden');")
    except:
        print("Couldn't disable sidebar on map")

    # Remove share
    try:
        element = BROWSER.find_element_by_xpath("//*[contains(text(), 'Share')]")
        BROWSER.execute_script(
            """
            var element = arguments[0];    
            element.parentNode.removeChild(element); 
            """,
            element,
        )
    except:
        print("Couldn't remove share button from map")

    # browser.execute_script("toggleFollow()")
    if enable_labels is True:
        BROWSER.find_element_by_tag_name("body").send_keys("l")

    if enable_track_labels is True:
        BROWSER.find_element_by_tag_name("body").send_keys("k")

    WebDriverWait(BROWSER, 40).until(
        lambda d: d.execute_script("return jQuery.active == 0")
    )

    try:
        photo_box = BROWSER.find_element_by_id("silhouette")
    except:
        pass
    else:
        photo_list = json.loads(
            requests.get(
                "https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/photo-list.json"
            ).text
        )
        if "icao" in url_params:
            icao = re.search("icao=(.+?)&", url_params).group(1).lower()
            print(icao)

            if icao in photo_list.keys():
                BROWSER.execute_script("arguments[0].id = 'airplanePhoto';", photo_box)
                BROWSER.execute_script(
                    f"arguments[0].src = 'https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/images/{photo_list[icao]['reg']}.jpg';",
                    photo_box,
                )
                copyright = BROWSER.find_element_by_id("copyrightInfo")
                BROWSER.execute_script(
                    "arguments[0].id = 'copyrightInfoFreeze';", copyright
                )
                BROWSER.execute_script(
                    "$('#copyrightInfoFreeze').css('font-size', '12px');"
                )
                BROWSER.execute_script(
                    f"arguments[0].appendChild(document.createTextNode('Image © {photo_list[icao]['photographer']}'))",
                    copyright,
                )

    time.sleep(5)
    BROWSER.save_screenshot(file_path)


def generate_adsbx_screenshot_time_params(timestamp):

    timestamp_dt = datetime.utcfromtimestamp(timestamp)
    print(timestamp_dt)
    start_time = timestamp_dt - timedelta(minutes=1)
    time_params = (
        f"&showTrace={timestamp_dt.strftime('%Y-%m-%d')}"
        f"&startTime={start_time.strftime('%H:%M:%S')}"
        f"&endTime={timestamp_dt.strftime('%H:%M:%S')}"
    )
    return time_params
