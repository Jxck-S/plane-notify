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
    browser.save_screenshot("map.png")
    browser.quit()