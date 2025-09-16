import time
from bs4 import BeautifulSoup
import mySecrets
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# TODO: pick camel or snake case - stop using both 
# camelCase - functions 
# PascalCase - Clases
# snake_case - variables 

def main() -> None:
    driver = setUpforSelenium()
    
    successful_login = logIntoWebsite(driver)

    if not successful_login:
        print("Login failed, exiting script.")
        driver.quit()
        return
    
    successful_navigation = navigateToRotaPage(driver)

    if not successful_navigation:
        print("Navigation to rota page failed, exiting script.")
        driver.quit()
        return
    
    driver.switch_to.default_content()
    driver.switch_to.frame("main")

    scraped_rota_data = useBS4ToScrapeFutureShifts(driver)
    scraped_past_rota_data = useBS4ToScrapePastShifts(driver, weeks=5)

    print(scraped_rota_data)
    print(scraped_past_rota_data)

    if scraped_rota_data:
        UpdateRotaSpreadsheet(scraped_rota_data)

    if scraped_past_rota_data:
        UpdateEarningPredition(scraped_past_rota_data)

def setUpGoogleAPI():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(mySecrets.google_account_creds_location, scope)
    client = gspread.authorize(creds)
    sheet = client.open(mySecrets.google_sheet_name).sheet1
    first_row = sheet.row_values(1)
    print(first_row)
    pass

def UpdateEarningPredition(past_rota_data):
    pass

def UpdateRotaSpreadsheet(scraped_rota_data):
    pass 

def navigateToRotaPage(driver) -> bool:
    try: 
        driver.switch_to.frame("main")
        driver.find_element(By.XPATH, "//*[@id='MainOakOptions']/div/a[1]/div").click()

        driver.switch_to.default_content()
        driver.switch_to.frame("side")

        time.sleep(1) # wait for frame to load
        search_bar = driver.find_element(By.XPATH, "//*[@id='search']/div/div/div[2]/div/div/div/div[2]/input")
        search_bar.click()
        search_bar.send_keys("my rota")
        search_bar.send_keys(Keys.RETURN)
        time.sleep(5) # wait for search results to load
        driver.find_element(By.XPATH, "//*[@id='searchResults']/div[1]/div/div/div/div").click()
        time.sleep(5) # wait for rota page to load
    except:
        return False

    return True

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

        FillInputField(driver, "Username", mySecrets.my_job_email)
        FillInputField(driver, "Password", mySecrets.my_job_password)
        time.sleep(10)  # Wait for 10 seconds to allow the page to load completely
    except:
        return False

    return True 

def scrapeRotaForTheWeek(page_source, week_start_date):
    soup = BeautifulSoup(page_source, "html.parser")
    results = {}

    for week_day in range(0,7):
        scrape_date = week_start_date + datetime.timedelta(days=week_day)
        day = scrape_date.day
        month = scrape_date.month
        year = scrape_date.year

        day_id = f'{day}-{month}-{year}-pamg{week_day}Contro{day}/{month}/{year}_0yrotam'

        rota_data_for_day = soup.find('div', id=day_id).parent.children
        day_div = [d for d in rota_data_for_day if d.name == 'div'][1].children # This grabs all the div children in a list form
        day_div = [d.get_text(strip=True) for d in day_div if d.name == 'div']

        # time is always 5 characters, including the colon
        for div in day_div:
            start_time_index = div.find(":") - 2
            start_time = div[start_time_index:start_time_index+5]
            end_time = div[start_time_index+6:start_time_index+11]

        if day_div:
            results[scrape_date] = {
                "start_time": start_time,
                "end_time": end_time
            }

    return results

def useBS4ToScrapePastShifts(driver, weeks=5):
    data = {}
    # look at 4 weeks in advance - 4th week is usually blank
    for week in range(weeks):
        
        driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]").click()
        time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today - datetime.timedelta(days=-today.weekday(), weeks=week)
        print(f"Scraping week starting: {week_start_date}")

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data.update(results)
    
    return data

def useBS4ToScrapeFutureShifts(driver):
    data = {}

    # look at 4 weeks in advance - 4th week is usually blank
    for week in range(4):
        if week != 0:
            driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[2]").click()
            time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today + datetime.timedelta(days=-today.weekday(), weeks=week)
        print(f"Scraping week starting: {week_start_date}") # add logger for these

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data.update(results)
    
    try: 
        driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]").click()
        time.sleep(1)
    except:
        print("error navigating back")
    
    return data


def FillInputField(driver, element_name, input_value) -> None:
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN) 

if __name__ == "__main__":
    # main()
    setUpGoogleAPI()
    pause = input("Press Enter to continue...") # Pause the script to allow user to see the browser for testing purposes
