import time
import requests
from bs4 import BeautifulSoup
import mySecrets
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options


def main():

    URL = mySecrets.my_job_website_url
    # print(f"Key : {mySecrets.my_job_website_url}")
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="ResultsContainer")
    if results:
        print(results.prettify())

    # clickLoginButton()

def setUpforSelenium():
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)
    return driver

def logIntoWebsite():  
    time.sleep(1)
    # driver = webdriver.Chrome()
    driver = setUpforSelenium()
    driver.get(mySecrets.my_job_website_url)



    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.NAME, "Username")
        )
    finally:
        # TODO: Split this into smaller functions, add error handling, navigate to payslip page. 
        FillInputField(driver, "Username", mySecrets.my_job_email)
        FillInputField(driver, "Password", mySecrets.my_job_password)


        time.sleep(10)  # seconds

        i_frame_elements = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Number of iframes on the page: {len(i_frame_elements)}")

        driver.switch_to.frame("main")
        # driver.find_element(By.ID, "MainOakOptions").click()  # works
        search = driver.find_element(By.XPATH, "//*[@id='MainOakOptions']/div/a[1]/div").click()

        i_frame_elements = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Number of iframes on the page: {len(i_frame_elements)}")

        print(i_frame_elements)
        driver.switch_to.default_content()
        driver.find_elements(By.TAG_NAME, "iframe")
        driver.switch_to.frame("side")
        time.sleep(5) # wait for frame to load
        search_bar = driver.find_element(By.XPATH, "//*[@id='search']/div/div/div[2]/div/div/div/div[2]/input")
        search_bar.click()
        search_bar.send_keys("my rota")
        search_bar.send_keys(Keys.RETURN)
        time.sleep(5) # wait for search results to load
        driver.find_element(By.XPATH, "//*[@id='searchResults']/div[1]/div/div/div/div").click()
        time.sleep(10) # wait for rota page to load




        time.sleep(10)  # Wait for 10 seconds to allow the page to load completely
        print("Page loaded")

    pause = input("Press Enter to continue...") # Pause the script to allow user to see the browser for testing purposes


def findElementByxPathAndWait(driver, xPath, timeout=10):
    while timeout > 0:
        try:
            element = driver.find_element(By.XPATH, xPath)
            return element
        except:
            time.sleep(1)
            timeout -= 1

def findElementAndWait(driver, by, value, timeout=10):
    while timeout > 0:
        try:
            element = driver.find_element(by, value)
            return element
        except:
            time.sleep(1)
            timeout -= 1

    print(f"Element searched by:  {by} = {value} \n not found within the timeout period.")
    return None

def FillInputField(driver, element_name, input_value):
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN) 

if __name__ == "__main__":
    logIntoWebsite()