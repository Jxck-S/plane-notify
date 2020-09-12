#https://pypi.org/project/selenium/
#https://zwbetz.com/download-chromedriver-binary-and-add-to-your-path-for-automated-functional-testing/
#https://pythonspot.com/selenium-take-screenshot/
#https://sites.google.com/a/chromium.org/chromedriver/downloads
#https://tecadmin.net/setup-selenium-with-chromedriver-on-debian/
#https://blog.testproject.io/2018/02/20/chrome-headless-selenium-python-linux-servers/
#https://serverfault.com/questions/172076/how-to-find-the-browser-versions-from-command-line-in-linux-windows
from selenium import webdriver
import time
def getSS(icao):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('window-size=800,800')
    #chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.
    browser = webdriver.Chrome(options=chrome_options)
    url = "https://globe.adsbexchange.com/?largeMode=2&hideButtons&hideSidebar&mapDim=0&zoom=9&icao=" + icao
    browser.get(url)
    time.sleep(30)
    file_name = icao + "_map.png"
    browser.save_screenshot(file_name)
    browser.quit()