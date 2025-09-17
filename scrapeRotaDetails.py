import time
from bs4 import BeautifulSoup
import mySecrets
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from enum import Enum
from gspread.utils import ValueInputOption
from gspread import Spreadsheet

class WeekDay(Enum):
    MONDAY = 0 
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    def string(cls):
        weekday = cls.name
        capitalised_weekday = weekday[0:1] + weekday[1:].lower()
        return str(capitalised_weekday)

class XPaths(Enum): 
    my_rota_last_week_btn = "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[1]"
    my_rota_next_week_btn = "/html/body/div[3]/div[1]/div[2]/div[4]/div[7]/div/div/div[2]/div/div/div/div[2]/div[1]/button[2]"
    search_result_my_rota = "//*[@id='searchResults']/div[1]/div/div/div/div"

class SpreadSheetEquations(Enum):

    @classmethod
    def hoursScheduled(cls, row_num):
            return f'=IF(D{row_num}-C{row_num} = 0 , 0,TIMEVALUE(D{row_num}-C{row_num})*24)'
    
    @classmethod
    def hoursWorked(cls, row_num):
            return f'=IF(G{row_num}-F{row_num} = 0 , 0,TIMEVALUE(G{row_num}-F{row_num})*24)'
    
    @classmethod
    def nightHoursWorked(cls, row_num):
            return f'=IF(C{row_num},IF(TIMEVALUE("06:00" - C{row_num})<0.25,TIMEVALUE("06:00" - C{row_num})*24,0),0)'
    
    @classmethod
    def nightHoursScheduled(cls, row_num):
            return f'=IF(F{row_num},IF(TIMEVALUE("06:00" - F{row_num})<0.25,TIMEVALUE("06:00" - F{row_num})*24,0),0)'
    

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
    navigate_back_to_this_week(driver)
    # scraped_past_rota_data = useBS4ToScrapePastShifts(driver, weeks=5)
    # print(scraped_past_rota_data)

    sheet = setUpGoogleAPI()

    if scraped_rota_data:
        UpdateRotaSpreadsheet(sheet, scraped_rota_data)
    # if scraped_past_rota_data:
    #     UpdateEarningPredition(scraped_past_rota_data)
    driver.quit()

def setUpGoogleAPI() -> Spreadsheet:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(mySecrets.google_account_creds_location, scope)
    client = gspread.authorize(creds)
    return client.open(mySecrets.google_sheet_name).worksheet("Worked hours - day ")

def rowValuesPreset(row_num: int, date: str, day_of_week: str, shift_start: str='', 
                    shift_end: str='', time_clocked_in: str='', time_clocked_out: str='') -> list[10]:
    return [date, 
            day_of_week, 
            shift_start,
            shift_end,
            SpreadSheetEquations.hoursScheduled(row_num),
            time_clocked_in, 
            time_clocked_out,
            SpreadSheetEquations.hoursWorked(row_num),
            SpreadSheetEquations.hoursScheduled(row_num),
            '', # Holiday 
            '', # day off
            SpreadSheetEquations.nightHoursScheduled]


def findLastDateWithScheduledShiftDataIndex(sheet: Spreadsheet, start_row: int = 2) ->  int:
    row = start_row
    not_found = True
    while not_found:
        first_cell = sheet.cell(row, 3).value
        if first_cell:
            return row
        row += 1
    print("Row not found")

def findDateRowIndex(sheet: Spreadsheet, start_row: int = 2, date: str=datetime.datetime.today().strftime("%d/%m/%y"), maxRowCheck: int = 50):
    row = start_row

    cell_list = sheet.range(f'A{start_row}:A{maxRowCheck}')
    for cell in cell_list:
        if cell.value == date:
            return True, row
        row = row + 1

    print("Row not found")
    return False, None

def addPresetFunctionsToNewRow(sheet: Spreadsheet, row_num: int) -> None:
    sheet.update_acell(f'E{row_num}', f'=IF(D{row_num}-C{row_num} = 0 , 0,TIMEVALUE(D{row_num}-C{row_num})*24)')
    sheet.update_acell(f'H{row_num}', f'=IF(G{row_num}-F{row_num} = 0 , 0,TIMEVALUE(G{row_num}-F{row_num})*24)')
    sheet.update_acell(f'L{row_num}', f'=IF(C{row_num},IF(TIMEVALUE("06:00" - C{row_num})<0.25,TIMEVALUE("06:00" - C{row_num})*24,0),0)')
    sheet.update_acell(f'I{row_num}', f'=IF(F{row_num},IF(TIMEVALUE("06:00" - F{row_num})<0.25,TIMEVALUE("06:00" - F{row_num})*24,0),0)')


def UpdateEarningPredition(past_rota_data):
    UpdateWorkedHours()
    UpdatePayExpectations()

def UpdateWorkedHours():
    pass

def UpdatePayExpectations():
    pass

def UpdateRotaSpreadsheet(sheet: Spreadsheet, scraped_rota_data):

    for week_index in scraped_rota_data:
        for day_index in scraped_rota_data[week_index]:

            date_str = scraped_rota_data[week_index][day_index]['date'].strftime("%d/%m/%y")
            week_day = scraped_rota_data[week_index][day_index]['day']
            start_time = scraped_rota_data[week_index][day_index]['start_time']
            end_time = scraped_rota_data[week_index][day_index]['end_time']

            # only update future dates
            print(f'{date_str} > {datetime.datetime.today().strftime("%d/%m/%y")} result: {(datetime.datetime.strptime(date_str, "%d/%m/%y").date() > datetime.date.today())}')
            if not (datetime.datetime.strptime(date_str, "%d/%m/%y").date() > datetime.date.today()):
                print(date_str)
                continue

            date_exists, row_num = findDateRowIndex(sheet, date=date_str)

            if row_num:
                use_row = row_num # set a row for when we reach new lines

            row_values = rowValuesPreset(use_row, date_str, week_day, start_time, end_time)
            # print(row_values)

            if date_exists and row_num:
                editRow(sheet, row_values, row_num, date_str)
            else:
                print(f'row number: {row_num}')
                print(f'use row: {use_row}')
                addRow(sheet, row_values, use_row, date_str)
                # sheet.insert_rows(values=[row_values], row=row_num)
        # TODO: match the date with the row number we need to add.
    
    # date + 1 - search for values in list, - add values to row, append to sheet 

def editRow(sheet: Spreadsheet, row_values, row_num, date):
    cell_list = sheet.range(f'A{row_num}:L{row_num}')
    i = 0
    for cell in cell_list:
        cell.value = row_values[i]
        i += 1
    sheet.update_cells(cell_list, value_input_option = ValueInputOption.user_entered)
    print(f"edit existting date: {date}")

def addRow(sheet: Spreadsheet, row_values, row_num, date):
    print(row_values)
    sheet.insert_row(row_values, row_num, value_input_option = ValueInputOption.user_entered) # TODO: Not working
    print(f"add new row for date: {date}")

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
        for div in day_div:
            start_time_index = div.find(":") - 2
            start_time = div[start_time_index:start_time_index+5]
            end_time = div[start_time_index+6:start_time_index+11]

        week_day
        # if day_div:
        results[week_day] = {
            "date" : scrape_date,
            "day" : WeekDay(scrape_date.weekday()).string(),
            "start_time": start_time,
            "end_time": end_time
        }

    return results

def generateDivId(day: int, month: int, year: int, week_day: int) -> str:
    return f'{day}-{month}-{year}-pamg{week_day}Contro{day}/{month}/{year}_0yrotam'

def useBS4ToScrapePastShifts(driver, weeks=5):
    data = {}

    for week in range(weeks):
        
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn).click()
        time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today - datetime.timedelta(days=-today.weekday(), weeks=week) # TODO: this does not work
        print(f"Scraping week starting: {week_start_date}")

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data[week] = results
    
    return data

def navigate_back_to_this_week(driver) -> None:
    try: 
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn).click()
        time.sleep(1)
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn).click()
        time.sleep(1)
        driver.find_element(By.XPATH, XPaths.my_rota_last_week_btn).click()
        time.sleep(1)
    except:
        failed_return = True
        print("error navigating back")

    if failed_return:
        try:
            driver.find_element(By.XPATH, XPaths.search_result_my_rota).click()
        except:
            print("error refreshing page")

def useBS4ToScrapeFutureShifts(driver) -> dict[int, dict[int, list]]:
    data = {}

    # look at 4 weeks in advance - 4th week is usually blank
    for week in range(4):
        if week != 0:
            driver.find_element(By.XPATH, XPaths.my_rota_next_week_btn).click()
            time.sleep(2) # wait for page to load

        today = datetime.date.today()
        week_start_date = today + datetime.timedelta(days=-today.weekday(), weeks=week)
        print(f"Scraping week starting: {week_start_date}") # add logger for these

        results = scrapeRotaForTheWeek(driver.page_source, week_start_date)
        data[week] = results
    
    return data


def FillInputField(driver, element_name, input_value) -> None:
    field_input = driver.find_element("name", element_name)
    field_input.send_keys(input_value)
    time.sleep(1) # wait for keys to be sent
    field_input.send_keys(Keys.RETURN) 

if __name__ == "__main__":
    main()
    pause = input("Press Enter to continue...") # Pause the script to allow user to see the browser for testing purposes
