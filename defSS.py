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
    WebDriverWait(browser, 40).until(lambda d: d.execute_script("return jQuery.active == 0"))
    time.sleep(5)
    remove_id_elements = ["show_trace", "credits", 'infoblock_close', 'selected_photo_link', "history_collapse"]
    for element in remove_id_elements:
        element = browser.find_element_by_id(element)
        browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
    element = browser.find_elements_by_class_name("infoHeading")
    browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element[19])
    #Remove watermark on data
    browser.execute_script("document.getElementById('selected_infoblock').className = 'none';")
    #Disable slidebar
    browser.execute_script("$('#infoblock-container').css('overflow', 'hidden');")
    #Remove share
    element = browser.find_element_by_xpath("//*[contains(text(), 'Share')]")
    browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
    #browser.execute_script("toggleFollow()")
    if enable_labels:
        browser.find_element_by_tag_name('body').send_keys('l')
    if enable_track_labels:
        browser.find_element_by_tag_name('body').send_keys('k')
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
def generate_adsbx_overlay_param(overlays):
    return "&overlays=" + ",".join(overlays)