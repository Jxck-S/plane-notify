"""
defSS.py: Selenium Screenshot Utility for TAR1090

This module provides functionality to take screenshots of TAR1090 flight tracking maps using Selenium and Chrome WebDriver.
It handles configuring the browser, navigating to the correct URL (configurable via config), modifying the page (hiding elements, adding credits), and capturing the screenshot.

Key Functions:
- get_tar1090_screenshot: Captures a screenshot of the TAR1090 map with specified parameters and overrides.
- generate_tar1090_screenshot_time_params: Generates URL parameters for a specific timestamp to show flight history.
- blur_elements_by_id: Helper to blur specific HTML elements for privacy/concealment.
"""
import json
from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import selenium.common.exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException 
from selenium.webdriver.support import expected_conditions as EC
import os
import platform
import requests, json
from datetime import datetime

from datetime import timedelta
import configparser

main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
def blur_elements_by_id(browser, element_ids):
        for element in element_ids:
            try:
                element = browser.find_element(By.ID, element)
                browser.execute_script("arguments[0].style.filter = 'blur(7px)';", element)
            except NoSuchElementException:
                print("Issue finding:", element, "on page")
def get_tar1090_screenshot(file_path, url_params, enable_labels=False, enable_track_labels=False, overrides={}, conceal_ac_id=False, conceal_pia=False, pia_active=False):
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=old")
        chrome_options.add_argument('window-size=1080,1080')
        chrome_options.add_argument('ignore-certificate-errors')
        chrome_options.page_load_strategy = 'normal'
        if platform.system() == "Linux":
            chrome_options.add_argument('crash-dumps-dir=/tmp/plane-notify/chrome')
            chrome_options.add_argument('user-data-dir=/tmp/plane-notify/chrome/user_data')

        #Plane images issue loading when in headless setting agent fixes.
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        if platform.system() == "Linux" and os.geteuid()==0:
            chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.

        browser = webdriver.Chrome(options=chrome_options)
        #Temp Fix for headless new https://stackoverflow.com/questions/75439784/chrome-headless-new-mode-does-not-allow-to-apply-window-size-option?rq=2
        #browser.set_window_size(1080, 1080+121)
        #browser.set_window_size(1080, 1080+121)
        tar1090_url = main_config.get('MAP', 'TAR1090_URL')
        url = f"{tar1090_url}/?{url_params}"
        print(f"Getting Screenshot of {url}")
        # for x in range(2):
        try:
            print("trying,")
            browser.get(url)
        except TimeoutException as e:
            pass
            #     print(e)
            #     if x == 1:
            #         raise(e)
            # else:
            #     break
        wait = WebDriverWait(browser, 50)
        try:
            wait.until(lambda browser: browser.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            pass
        try:
            WebDriverWait(browser, 15).until(lambda d: d.execute_script("return window.jQuery != undefined"))
        except TimeoutException as e:
            print(e)
        else:
            try:
                WebDriverWait(browser, 20).until(lambda d: d.execute_script("return jQuery.active == 0"))
            except TimeoutException as e:
                print("Handled fail on webdriver wait for jQuery not active")
        try:
            WebDriverWait(browser, 50).until(lambda browser: browser.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            raise(e)
            pass
        remove_id_elements = ["show_trace", 'infoblock_close', 'selected_photo_link', "history_collapse", "tracking_leaderboard_container", "feature_landings"]
        credits_option = "replace"
        text_credit = main_config.get('MAP', 'TEXT_CREDIT')
        credit_img_url = main_config.get('MAP', 'CREDIT_IMG_URL')
        browser.execute_script(f"$('#credits').css('left', 'calc(88% - 60px * var(--SCALE))');")
        browser.execute_script(f"$('#credits').css('bottom', 'calc( 25px * var(--SCALE))');")
        browser.execute_script(f"$('#credits').css('opacity', '1');")
        browser.execute_script(f"$('.credits-image').css('opacity', '1');")
        browser.execute_script(f"$('#credits').css('font-weight', '600');")
        browser.execute_script(f"$('#credits').css('color', 'black');")
        if credits_option == "remove":
            remove_id_elements += ['credits', 'creditsSelected']
        elif credits_option == "replace":
            credits_text = browser.find_elements(By.CLASS_NAME, "credits-text")
            for elem in credits_text:
                browser.execute_script(f"arguments[0].innerText = '{text_credit}';", elem)
            browser.execute_script(f"$('.credits-image').css('background-image', 'url({credit_img_url})');")
        for element in remove_id_elements:
            try:
                element = browser.find_element(By.ID, element)
                browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
            except:
                print("Issue finding:", element, "on page")
        #Remove watermark on data
        try:
            browser.execute_script("document.getElementById('selected_infoblock').className = 'none';")
        except:
            print("Couldn't remove watermark from map")
        #Disable slidebar
        try:
            browser.execute_script("$('#infoblock-container').css('overflow', 'hidden');")
        except:
            print("Couldn't disable sidebar on map")
        #Remove Copy Link
        try:
            element = browser.find_element(By.XPATH, "//*[@id='selected_icao']/span[2]/a")
            browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
        except Exception as e:
            print("Couldn't remove copy link button from map", e)
        #Recolor
        colored_border = browser.find_elements(By.CLASS_NAME, "highlightedTitle")
        for border in colored_border:
            browser.execute_script("arguments[0].style.borderBottom = 'solid #6b0d0d';", border)

        colored_headers = browser.find_elements(By.CLASS_NAME, "sectionTitle")
        for header in colored_headers:
            browser.execute_script("arguments[0].style.background = '#6b0d0d';", header)
        #browser.execute_script("toggleFollow()")
        if conceal_pia or conceal_ac_id:
            blur_elements_by_id(browser, ["selected_callsign", "selected_icao", "selected_squawk1"])
        if conceal_ac_id:
            blur_elements_by_id(browser, ["selected_registration", "selected_country", "selected_dbFlags", "selected_ownop", "selected_typelong", "selected_icaotype", "airplanePhoto", "silhouette", "copyrightInfo"])
        if enable_labels:
            browser.execute_script("toggleLabels();")
        if enable_track_labels:
            browser.execute_script("toggleTrackLabels();")
        else:
            #Ensure its off sometimes it's not? bug?
            trackLabels = browser.execute_script("return trackLabels;")
            if trackLabels:
                trackLabels = browser.execute_script("toggleTrackLabels();")
        if pia_active and 'reg' in overrides.keys():
            element = browser.find_element(By.ID, "selected_registration")
            browser.execute_script(f"arguments[0].innerText = '* {overrides['reg']}'", element)
            reg = overrides['reg']
        else:
            try:
                reg = browser.find_element(By.ID, "selected_registration").get_attribute("innerHTML")
                print("Reg from tar1090 is", reg)
            except Exception as e:
                print("Couldn't find reg in tar1090", e)
                reg = None
        if reg is not None:
            try:
                try:
                    photo_box = browser.find_element(By.ID, "silhouette")
                except NoSuchElementException:
                    photo_box = browser.find_element(By.ID, "airplanePhoto")
                finally:
                    photo_list = json.loads(requests.get("https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/photo-list.json", timeout=20).text)
                    if reg in photo_list.keys():
                        browser.execute_script("arguments[0].id = 'airplanePhoto';", photo_box)
                        #browser.execute_script("arguments[0].removeAttribute('width')", photo_box)
                        #browser.execute_script("arguments[0].style.width = '200px';", photo_box)
                        #browser.execute_script("arguments[0].style.float = 'left';", photo_box)
                        browser.execute_script(f"arguments[0].src = 'https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/images/{reg}.jpg';", photo_box)
                        image_copy_right = browser.find_element(By.ID, "copyrightInfo")
                        copy_right_children = image_copy_right.find_elements(By.XPATH, "*")
                        if len(copy_right_children) > 0:
                            browser.execute_script(f"arguments[0].innerText = 'Image © {photo_list[reg]['photographer']}'", copy_right_children[0])
                        else:
                            browser.execute_script(f"arguments[0].appendChild(document.createTextNode('Image © {photo_list[reg]['photographer']}'))", image_copy_right)


                    try:
                        WebDriverWait(browser, 40).until(lambda d: d.execute_script("return arguments[0].complete == true", photo_box))
                    except TimeoutException as e:
                        print(f"Aircraft: {photo_box.get_attribute('id')} didn't load from {browser.execute_script('return arguments[0].src', photo_box)}")
                        #Clears copyright if image didn't load
                        image_copy_right = browser.find_element(By.ID, "copyrightInfo")
                        copy_right_children = image_copy_right.find_elements(By.XPATH, "*")
                        if len(copy_right_children) > 0:
                            browser.execute_script(f"arguments[0].innerText = ''", copy_right_children[0])
            except Exception as e:
                print("Error on changing photo", e)

            try:
                WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.credits-image')))
            except TimeoutException as e:
                print(f"Credits image didn't load")
        if pia_active:
            if 'type' in overrides.keys():
                element = browser.find_element(By.ID, "selected_icaotype")
                browser.execute_script(f"arguments[0].innerText = '* {overrides['type']}'", element)
            if 'typelong' in overrides.keys():
                element = browser.find_element(By.ID, "selected_typelong")
                browser.execute_script(f"arguments[0].innerText = '* {overrides['typelong']}'", element)
            if 'ownop' in overrides.keys():
                element = browser.find_element(By.ID, "selected_ownop")
                browser.execute_script(f"arguments[0].innerText = '* {overrides['ownop']}'", element)
        try:
            WebDriverWait(browser, 15).until(lambda browser: browser.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            pass
        browser.execute_cdp_cmd('Emulation.setScriptExecutionDisabled', {'value': True})
        browser.save_screenshot(file_path)
        browser.quit()
    except selenium.common.exceptions.WebDriverException as e:
        print(f"Screenshot failed {e}")
        # Get the current date and time in the desired format
        current_time = datetime.now().strftime('%Y-%m-%d__%H_%M_%S')
        
        # Construct the file name with the current date and time
        file_name = f"./logs/screenshot_logs/{current_time}.log"

        # Write the exception information to the log file
        with open(file_name, 'a') as file:
            file.write(f'[{current_time}] Screenshot error occurred: {str(e)}\n')
def generate_tar1090_screenshot_time_params(timestamp):
    timestamp_dt = datetime.utcfromtimestamp(timestamp)
    print(timestamp_dt)
    start_time = timestamp_dt - timedelta(minutes=1)
    time_params = "&showTrace=" + timestamp_dt.strftime("%Y-%m-%d")  + "&startTime=" + start_time.strftime("%H:%M:%S") + "&endTime=" + timestamp_dt.strftime("%H:%M:%S")
    return time_params
