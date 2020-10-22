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
def getSS(icao):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument('window-size=800,800')
    chrome_options.add_argument('ignore-certificate-errors')
    chrome_options.add_argument("--enable-logging --v=1")
    #chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    url = "https://globe.adsbexchange.com/?largeMode=2&hideButtons&hideSidebar&mapDim=0&zoom=9&icao=" + icao
    browser.set_page_load_timeout(80)
    browser.get(url)
    WebDriverWait(browser, 10).until(lambda d: d.execute_script("return jQuery.active == 0"))
    file_name = icao + "_map.png"
    browser.save_screenshot(file_name)
    browser.quit()