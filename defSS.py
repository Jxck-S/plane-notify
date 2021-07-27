from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
def get_adsbx_screenshot(file_path, url_params, enable_labels=False, enable_track_labels=False):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument('window-size=800,800')
    chrome_options.add_argument('ignore-certificate-errors')
    chrome_options.add_argument("--enable-logging --v=1")
    import os
    import platform
    if platform.system() == "Linux" and os.geteuid()==0:
        chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    url = f"https://globe.adsbexchange.com/?{url_params}"
    browser.set_page_load_timeout(80)
    browser.get(url)
    remove_id_elements = ["show_trace", "credits", 'infoblock_close', 'selected_photo_link', "history_collapse"]
    for element in remove_id_elements:
        try:
            element = browser.find_element_by_id(element)
            browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
        except:
            print("issue removing", element, "from map")
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
    #Remove share
    try:
        element = browser.find_element_by_xpath("//*[contains(text(), 'Share')]")
        browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
    except:
        print("Couldn't remove share button from map")
    #browser.execute_script("toggleFollow()")
    if enable_labels:
        browser.find_element_by_tag_name('body').send_keys('l')
    if enable_track_labels:
        browser.find_element_by_tag_name('body').send_keys('k')
    WebDriverWait(browser, 40).until(lambda d: d.execute_script("return jQuery.active == 0"))
    try:
        photo_box = browser.find_element_by_id("silhouette")
    except:
        pass
    else:
        import requests, json
        photo_list = json.loads(requests.get("https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/photo-list.json").text)
        if "icao" in url_params:
            import re

            icao = re.search('icao=(.+?)&', url_params).group(1).lower()
            print(icao)
            if icao in photo_list.keys():
                browser.execute_script("arguments[0].id = 'airplanePhoto';", photo_box) 
                browser.execute_script(f"arguments[0].src = 'https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/images/{photo_list[icao]['reg']}.jpg';", photo_box) 
                copyright = browser.find_element_by_id("copyrightInfo")
                browser.execute_script("arguments[0].id = 'copyrightInfoFreeze';", copyright) 
                browser.execute_script("$('#copyrightInfoFreeze').css('font-size', '12px');")
                browser.execute_script(f"arguments[0].appendChild(document.createTextNode('Image © {photo_list[icao]['photographer']}'))", copyright)

    time.sleep(5)
    browser.save_screenshot(file_path)
    browser.quit()
def generate_adsbx_screenshot_time_params(timestamp):
    from datetime import datetime
    from datetime import timedelta
    timestamp_dt = datetime.utcfromtimestamp(timestamp)
    print(timestamp_dt)
    start_time = timestamp_dt - timedelta(minutes=1)
    time_params = "&showTrace=" + timestamp_dt.strftime("%Y-%m-%d")  + "&startTime=" + start_time.strftime("%H:%M:%S") + "&endTime=" + timestamp_dt.strftime("%H:%M:%S")
    return time_params