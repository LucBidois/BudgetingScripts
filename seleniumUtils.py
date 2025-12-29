import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def setUpforSelenium() -> webdriver.Chrome:
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)
    return driver

def logIntoWebsite(driver: webdriver.Chrome, url, email, password) -> bool:  
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.NAME, "Username")
        )

        FillInputField(driver, "Username", email)
        FillInputField(driver, "Password", password)
        time.sleep(10)  # Wait for 10 seconds to allow the page to load completely
    except:
        return False

    return True 

def FillInputField(driver: webdriver.Chrome, element_name, input_value) -> None:
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN)