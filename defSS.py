#https://pypi.org/project/selenium/
#https://zwbetz.com/download-chromedriver-binary-and-add-to-your-path-for-automated-functional-testing/
#https://pythonspot.com/selenium-take-screenshot/
#https://sites.google.com/a/chromium.org/chromedriver/downloads
#https://tecadmin.net/setup-selenium-with-chromedriver-on-debian/
#https://blog.testproject.io/2018/02/20/chrome-headless-selenium-python-linux-servers/
#https://serverfault.com/questions/172076/how-to-find-the-browser-versions-from-command-line-in-linux-windows
#https://pypi.org/project/webdriver-manager/
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
def getSS(icao, overlays):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument('window-size=800,800')
    chrome_options.add_argument('ignore-certificate-errors')
    chrome_options.add_argument("--enable-logging --v=1")
    import os
    if os.geteuid()==0:
        chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    url = "https://globe.adsbexchange.com/?largeMode=2&hideButtons&hideSidebar&mapDim=0&zoom=9&icao=" + icao + "&" + overlays
    browser.set_page_load_timeout(80)
    browser.get(url)
    WebDriverWait(browser, 40).until(lambda d: d.execute_script("return jQuery.active == 0"))
    time.sleep(5)
    remove_elements = ["show_trace", "credits", 'infoblock_close', 'selected_photo_link', "history_collapse"]
    for element in remove_elements:
        element = browser.find_element_by_id(element)
        browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
    #Remove watermark on data
    browser.execute_script("document.getElementById('selected_infoblock').className = 'none';")
    #Disable slidebar
    browser.execute_script("$('#infoblock-container').css('overflow', 'hidden');")
    #Remove share
    element = browser.find_element_by_xpath("//*[contains(text(), 'Share')]")
    browser.execute_script("""var element = arguments[0];    element.parentNode.removeChild(element); """, element)
    #browser.execute_script("toggleFollow()")
    file_name = icao + "_map.png"
    browser.save_screenshot(file_name)
    browser.quit()