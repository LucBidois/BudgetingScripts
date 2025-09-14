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

def main() -> None:
    driver = setUpforSelenium()
    
    successfulLogin = logIntoWebsite(driver)

    if not successfulLogin:
        print("Login failed, exiting script.")
        driver.quit()
        return
    
    successfulNavigation = navigateToRotaPage(driver)

    if not successfulNavigation:
        print("Navigation to rota page failed, exiting script.")
        driver.quit()
        return
    
    driver.switch_to.default_content()
    driver.switch_to.frame("main")

    # I want to return a list of dates with, starttime and endtime - I want to next 4 weeks.
    scrapedRotaData = useBS4ToScrapeDataEachWeek(driver, driver.page_source)

    UpdateRotaSpreadsheet(scrapedRotaData)

    time.sleep(10)  # Wait for 10 seconds to allow the page to load completely
    print("Page loaded")

def UpdateRotaSpreadsheet(scrapedRotaData) -> bool:
    return False # True if successful, False if not

def navigateToRotaPage(driver) -> bool:
    # i_frame_elements = driver.find_elements(By.TAG_NAME, "iframe")
    # print(f"Number of iframes on the page: {len(i_frame_elements)}")

    driver.switch_to.frame("main")
    driver.find_element(By.XPATH, "//*[@id='MainOakOptions']/div/a[1]/div").click()

    # i_frame_elements = driver.find_elements(By.TAG_NAME, "iframe")
    # print(f"Number of iframes on the page: {len(i_frame_elements)}")

    driver.switch_to.default_content()
    # driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame("side")

    time.sleep(1) # wait for frame to load
    search_bar = driver.find_element(By.XPATH, "//*[@id='search']/div/div/div[2]/div/div/div/div[2]/input")
    search_bar.click()
    search_bar.send_keys("my rota")
    search_bar.send_keys(Keys.RETURN)
    time.sleep(5) # wait for search results to load
    driver.find_element(By.XPATH, "//*[@id='searchResults']/div[1]/div/div/div/div").click()
    time.sleep(5) # wait for rota page to load

    return True
    # TODO: Test if rota page has loaded correctly, return True/False

def setUpforSelenium() -> webdriver.Chrome:
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)
    return driver

def logIntoWebsite(driver) -> bool:  
    driver.get(mySecrets.my_job_website_url)
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.NAME, "Username")
        )
    finally:
        FillInputField(driver, "Username", mySecrets.my_job_email)
        FillInputField(driver, "Password", mySecrets.my_job_password)
        time.sleep(10)  # Wait for 10 seconds to allow the page to load completely
        return True
        # TODO: Check if login was successful return True/False


def useBS4ToScrapeDataEachWeek(driver, page_source):
    data = [] # TODO: Change to appropriate data structure
    print("Using BeautifulSoup to scrape data...")
    soup = BeautifulSoup(page_source, "html.parser")
    results = soup.find(id="pageControl_myrota")

    for day in range(0,7):
        date = 8 + day # TODO: Change to dynamic date, month, year
        month = 9 
        year = 2025

        day_id = f'{date}-{month}-{year}-pamg{day}Contro{date}/{month}/{year}_0yrotam'

        print(day_id)

        # TODO: rethink variable names for readability improvement
        day_div = soup.find('div', id=day_id).parent.children
        day_div = [d for d in day_div if d.name == 'div'][1].children # This grabs all the div children in a list form
        day_div = [d.get_text(strip=True) for d in day_div if d.name == 'div']

        # TODO: filter out unwanted text from day_div

        data.append(day_div)
    return data


def FillInputField(driver, element_name, input_value) -> None:
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN) 

if __name__ == "__main__":
    main()
    pause = input("Press Enter to continue...") # Pause the script to allow user to see the browser for testing purposes
