import time
import datetime
from enum import Enum
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.utils import ValueInputOption
from gspread import Worksheet

from googleSheet import PaySlipSheetUtils
import mySecrets

class WeekDay(Enum):
    MONDAY = 0 
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def string(self):
        weekday = self.name
        capitalised_weekday = weekday[0:1] + weekday[1:].lower()
        return str(capitalised_weekday)

class XPaths(Enum): 
    my_rota_last_week_btn = "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]"
    my_rota_next_week_btn = "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[2]"
    search_result_my_rota = "//*[@id='searchResults']/div[1]/div/div/div/div"
    search_bar = "//*[@id='search']/div/div/div[2]/div/div/div/div[2]/input"
    search_window = "//*[@id='MainOakOptions']/div/a[1]/div"

class SpreadSheetEquations(Enum):

    @classmethod
    def hoursScheduled(cls, row_num: int) -> str:
        return f'=IF(D{row_num}-C{row_num} = 0 , 0,TIMEVALUE(D{row_num}-C{row_num})*24)'

    @classmethod
    def hoursWorked(cls, row_num: int) -> str:
        return f'=IF(G{row_num}-F{row_num} = 0 , 0,TIMEVALUE(G{row_num}-F{row_num})*24)'
    
    @classmethod
    def nightHoursWorked(cls, row_num: int) -> str:
        return f'=IF(F{row_num},IF(TIMEVALUE("06:00" - F{row_num})<0.25,TIMEVALUE("06:00" - F{row_num})*24,0),0)'
    
    @classmethod
    def nightHoursScheduled(cls, row_num: int) -> str:
        return f'=IF(C{row_num},IF(TIMEVALUE("06:00" - C{row_num})<0.25,TIMEVALUE("06:00" - C{row_num})*24,0),0)'
 

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

    scraped_scheduled_rota_data = useBS4ToScrapeFutureShifts(driver)
    navigate_back_to_this_week(driver)
    scrape_past_weeks_num = 5
    scraped_past_rota_data = useBS4ToScrapePastShifts(driver, weeks=scrape_past_weeks_num)

    payslip_utils = PaySlipSheetUtils()
    worksheet_data, worksheet_class = payslip_utils.getWorksheet()

    # add worked shift information
    sheet_values_past, edit_range_past = payslip_utils.prepareUpdateWorkedHours(worksheet_data, scraped_past_rota_data, scrape_past_weeks_num)
    payslip_utils.updateWorksheet(worksheet_class, sheet_values_past, edit_range_past)

    # add work schedule information
    sheet_values_future_A_E, sheet_values_future_H_L, sheet_values_future_insert, last_row, first_row  = payslip_utils.prepareUpdateScheduledHours(worksheet_data, scraped_scheduled_rota_data)
    payslip_utils.updateWorksheet(worksheet_class, sheet_values_future_A_E, f"A{first_row}:E{last_row}")
    payslip_utils.updateWorksheet(worksheet_class, sheet_values_future_H_L, f"H{first_row}:L{last_row}")

    worksheet_class.insert_rows(values=sheet_values_future_insert, row=first_row, value_input_option=ValueInputOption.user_entered)

    driver.quit()

def setUpGoogleAPI() -> Worksheet:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(mySecrets.google_account_creds_location, scope)
    client = gspread.authorize(creds)
    return client.open(mySecrets.google_income_worksheet_name).worksheet("Worked hours - day ")

def rowValuesPreset(row_num: int, date: str, day_of_week: str, shift_start: str='',
                    shift_end: str='', time_clocked_in: str='', time_clocked_out: str='',
                    holiday: str='') -> list[str]:
    return [date,
            day_of_week,
            shift_start,
            shift_end,
            SpreadSheetEquations.hoursScheduled(row_num),
            time_clocked_in,
            time_clocked_out,
            SpreadSheetEquations.hoursWorked(row_num),
            SpreadSheetEquations.nightHoursWorked(row_num),
            holiday, # Holiday
            '', # day off
            SpreadSheetEquations.nightHoursScheduled(row_num)]

def navigateToRotaPage(driver: webdriver.Chrome) -> bool:
    try: 
        driver.switch_to.frame("main")
        driver.find_element(By.XPATH, XPaths.search_window.value).click()

        driver.switch_to.default_content()
        driver.switch_to.frame("side")

        time.sleep(1) # wait for frame to load
        search_bar = driver.find_element(By.XPATH, XPaths.search_bar.value)
        search_bar.click()
        search_bar.send_keys("my rota")
        search_bar.send_keys(Keys.RETURN)
        time.sleep(5) # wait for search results to load
        driver.find_element(By.XPATH, XPaths.search_result_my_rota.value).click()
        time.sleep(5) # wait for rota page to load
    except Exception:
        return False

    return True

def setUpforSelenium() -> webdriver.Chrome:
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)
    return driver

def logIntoWebsite(driver: webdriver.Chrome) -> bool:  
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

def scrapeRotaForTheWeek(page_source, week_start_date) -> dict[int, dict]:
    soup = BeautifulSoup(page_source, "html.parser")
    results = {}

    for week_day in range(0,7):
        start_time, end_time = "", "" # reset values if not populated
        scrape_date = week_start_date + datetime.timedelta(days=week_day)
        day = scrape_date.day
        month = scrape_date.month
        year = scrape_date.year

        day_id = f'{day}-{month}-{year}-pamg{week_day}Contro{day}/{month}/{year}_0yrotam'

        rota_data_for_day = soup.find('div', id=day_id).parent.children
        day_div = [d for d in rota_data_for_day if d.name == 'div'][1].children # This grabs all the div children in a list form
        day_div = [d.get_text(strip=True) for d in day_div if d.name == 'div']

        # time is always 5 characters, including the colon
        if day_div and not (day_div[0][0:7] == "Holiday") and not (day_div[0][0:11] == "Unpaid Sick"):
            start_time_index = day_div[0].find(":") - 2
            start_time = day_div[0][start_time_index:start_time_index+5]
            end_time_index = day_div[-1].find(":") - 2
            end_time = day_div[-1][end_time_index+6:end_time_index+11]

        if day_div and day_div[0][0:7] == "Holiday":
            holiday = '1' # magic values match spreadsheet
        else:
            holiday = ''

        results[week_day] = {
            "date" : scrape_date,
            "day" : WeekDay(scrape_date.weekday()).string(),
            "start_time": start_time,
            "end_time": end_time,
            "holiday": holiday
        }

    return results

def generateDivId(day: int, month: int, year: int, week_day: int) -> str:
    return f'{day}-{month}-{year}-pamg{week_day}Contro{day}/{month}/{year}_0yrotam'

def useBS4ToScrapePastShifts(driver: webdriver.Chrome, weeks: int=5) -> dict[int, dict[int, list]]:
    data = {}

    for week in range(weeks):

        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn.value).click()
        time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today + datetime.timedelta(days=-today.weekday(), weeks=-week - 1)
        print(f"Scraping week starting: {week_start_date}") # scraping week ending?? 

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data[week] = results
    return data

def navigate_back_to_this_week(driver: webdriver.Chrome) -> None:
    try: 
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn.value).click()
        time.sleep(1)
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn.value).click()
        time.sleep(1)
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn.value).click()
        time.sleep(1)
        return
    except Exception:
        failed_return = True
        print("error navigating back")

    if failed_return:
        try:
            driver.find_element(By.XPATH, XPaths.search_result_my_rota.value).click()
        except Exception:
            print("error refreshing page")

def useBS4ToScrapeFutureShifts(driver: webdriver.Chrome, check_weeks : int = 4) -> dict[int, dict[int, list]]:
    data = {}

    for week in range(check_weeks):
        if week != 0:
            driver.find_element(By.XPATH, XPaths.my_rota_next_week_btn.value).click()
            time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today + datetime.timedelta(days=-today.weekday(), weeks=week)
        print(f"Scraping week starting: {week_start_date}")

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data[week] = results

    return data


def FillInputField(driver: webdriver.Chrome, element_name, input_value) -> None:
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN)

if __name__ == "__main__":
    main()
    # Pause the script to allow user to see the browser for testing purposes
    # pause = input("Press Enter to continue...")
