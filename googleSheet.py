"""
EDITING mySecrets.google_income_page_2_name page

Use a 2D array as an input to edit a matching area of the spreadsheet. 
- match the row that we start on and the row that we end on, knowing where we also need to add new rows. 
- We already know the range of columns we are looking at. A-L 

- when adding new row - either we need to learn how to add a large block using one request or we need to loop with a try except that waits out the API call limit
"""

"""
EDITING "Payday expectations"

- input comes from mySecrets.google_income_page_2_name 
- one call request taking only the rows for the months we want to look at
- one call for the current state of this sheet
- Make all the edits that I nee
    - Need to get info from the payslips page (only need to update once a month)
    - prepare all functions and formulas that pull from mySecrets.google_income_page_2_name
"""

import datetime
from enum import Enum
from gspread import Spreadsheet
from gspread.utils import ValueInputOption
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import mySecrets

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

class GoogleSpreadSheetUtils():
    """
    Class holding general methods and attributes that are useful on any spreadsheet projects. 
    """
    def setUpGoogleAPI(self, 
                       worksheet_name: str, 
                       worksheet_page_name: str, 
                       google_creds: str=mySecrets.google_account_creds_location) -> Spreadsheet:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(google_creds, scope)
        client = gspread.authorize(creds)
        return client.open(worksheet_name).worksheet(worksheet_page_name)

    def readSpreadsheet(self, worksheet: Spreadsheet, range: str) -> list[list]:
        return worksheet.get(range)
    
    def debugPrintSpreadsheetValues(self, input):
        for i in input:
            print(i)

class PaySlipSheetUtils():
    """
    Class holding methods and attributs only used by my pay and rota tracking spreadsheet
    """
    def getWorksheet(self, worksheet_name: str = mySecrets.google_income_worksheet_name, page_name:  str = mySecrets.google_income_page_2_name, range: str = "A1:L") -> {list[list], Spreadsheet.worksheet}:
        g_utils = GoogleSpreadSheetUtils()
        sheet = g_utils.setUpGoogleAPI(worksheet_name, page_name)
        return g_utils.readSpreadsheet(sheet, range), sheet

    def prepareUpdateScheduledHours(self, worksheet:list, scraped_scheduled_data: dict[int, dict[int, dict[str, str]]]):
        sheet_values_A_to_E = []
        sheet_values_H_to_L = []
        sheet_values_new_rows = []
        new_row = 0
        # first_date_row_found = False
        first_row = 0

        for week_index in scraped_scheduled_data:
            for day_index in scraped_scheduled_data[week_index]:
            
                date_str = scraped_scheduled_data[week_index][day_index]['date'].strftime("%d/%m/%y")
                week_day = scraped_scheduled_data[week_index][day_index]['day']
                start_time = scraped_scheduled_data[week_index][day_index]['start_time']
                end_time = scraped_scheduled_data[week_index][day_index]['end_time']
                holiday = scraped_scheduled_data[week_index][day_index]['holiday']

                # only update future dates
                if datetime.date.today() > datetime.datetime.strptime(date_str, "%d/%m/%y").date():
                    print(f"skipping {date_str} as it is in the past.")
                    continue
                
                date_exists, row_num = self.findDateRowIndex(worksheet, date=date_str)

                if row_num:
                    last_editable_row = row_num + 1

                if not first_row:
                    first_row = row_num + 1

                if date_exists and row_num:
                    sheet_values_A_to_E.append(self.rowValues(row_num + 1, date_str, week_day, shift_start=start_time, shift_end=end_time, holiday=holiday)[0:5]) 
                    sheet_values_H_to_L.append(self.rowValues(row_num + 1, date_str, week_day, shift_start=start_time, shift_end=end_time, holiday=holiday)[7:12])
                else:
                    if not new_row:
                        new_row = row_num
                    else:
                        new_row += 1
                    sheet_values_new_rows.append(self.rowValues(new_row, date_str, week_day, shift_start=start_time, shift_end=end_time, holiday=holiday))


        return sheet_values_A_to_E[::-1], sheet_values_H_to_L[::-1], sheet_values_new_rows[::-1], first_row, last_editable_row

    def prepareUpdateWorkedHours(self, worksheet: list, scraped_rota_data: dict[int, dict[int,dict[str, str]]], weeks_scraped: int):
        sheet_values = []
        first_date_row_found = False
        for week_index in range(weeks_scraped)[::-1]:
            for day_index in scraped_rota_data[week_index]:

                date_str = scraped_rota_data[week_index][day_index]['date'].strftime("%d/%m/%y")
                week_day = scraped_rota_data[week_index][day_index]['day']
                start_time = scraped_rota_data[week_index][day_index]['start_time']
                end_time = scraped_rota_data[week_index][day_index]['end_time']
                holiday = scraped_rota_data[week_index][day_index]['holiday']

                # only update past dates
                if datetime.date.today() < datetime.datetime.strptime(date_str, "%d/%m/%y").date():
                    print(f'date: {date_str} is from the future, skipping')
                    continue
                
                if not first_date_row_found:
                    date_exists, row_num = self.findDateRowIndex(worksheet, date=date_str)
                    first_date_row_found = True
                    first_row = row_num
                else: 
                    row_num -= 1
                
                if date_exists and row_num:
                    sheet_values.append(self.rowValues(row_num + 1, date_str, week_day, time_clocked_in=start_time, time_clocked_out=end_time, holiday=holiday)[5:12])

        if date_exists and row_num:
            edit_range = f'F{row_num + 1}:L{first_row + 1}'
            return sheet_values[::-1], edit_range
            # sheet.update(sheet_values, edit_range, value_input_option = ValueInputOption.user_entered )

    def updateWorksheet(self, spreadsheet, sheet_values, edit_range):
        spreadsheet.update(sheet_values, edit_range, value_input_option = ValueInputOption.user_entered )


    def rowValues(self, row_num: int, date: str, day_of_week: str, shift_start: str='',
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

    def findDateRowIndex(self, worksheet: list, date: str=datetime.datetime.today().strftime("%d/%m/%y")):

        for row in range(len(worksheet)):
            if worksheet[row][0] == date:
                return True, row

        print(f"Row not found for date {date}")
        return False, None

    def editRow(self, sheet: Spreadsheet, row_values, row_num, date, edit_schedule: bool = False, edit_clock_in: bool = False) -> None:
    # print(row_values)
        if edit_schedule: 
            cell_range = sheet.range(f'A{row_num}:L{row_num}')
            cell_list = self.setCellValues(cell_range, row_values)

        elif edit_clock_in:
            cell_list_0 = sheet.range(f'A{row_num}:B{row_num}')
            cell_list_1 = sheet.range(f'E{row_num}:L{row_num}')
            row_values_0 = row_values[0:2]
            row_values_1 = row_values[4:]
            cell_list = self.setCellValues(cell_list_0, row_values_0) + self.setCellValues(cell_list_1, row_values_1)

        sheet.update_cells(cell_list, value_input_option = ValueInputOption.user_entered) # TODO: investigate issue
        print(f"edit existting date: {date}")

    def setCellValues(self, cell_list, row_values):
        i=0
        for cell in cell_list:
            cell.value = row_values[i]
            i += 1
        return cell_list
    
    def test(self):

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(mySecrets.google_account_creds_location, scope)
        client = gspread.authorize(creds)
        sheet = client.open(mySecrets.google_income_worksheet_name)
        worksheet = sheet.worksheet(mySecrets.google_income_page_2_name)

        # worksheet_values, sheet = self.getWorksheet(mySecrets.google_income_worksheet_name, mySecrets.google_income_page_2_name)
        print(sheet)
        values = [['testing', '', '', '', '', '', '', '', '', '', 'testing2'], ['testing3', '', '', '', '', '', 'hello', '', '', '', 'testing4']]
        # sheet.batch_update()
        # sheet.values_append(range = 'Worked hours - day!A6:L6', params = {'valueInputOption': 'USER_ENTERED', 'insertDataOption' : 'INSERT_ROWS'}, body = {'values': values}) # this has updated at the bottom...
        # worksheet.append_rows() # this will also only add rows at the end of the table. 
        # worksheet.insert_cols(values= values, col = 6, value_input_option= ValueInputOption.user_entered)
        worksheet.insert_rows(values= values, row = 6, value_input_option= ValueInputOption.user_entered)


class BudgetingSheetUtils():
    """
    Class holding methods and attributes used in my budget spreadsheet. 
    Child classes may include
    - Mortgage tracker 
    - Taxes dependent on income changes
    - Monthly expectations of expenses
    - Tracking expenses
    - Using Reciepts to auto update and track expenses 
    """

if __name__ == "__main__":
    # payslip = PaySlipSheetUtils()
    # payslip.test()
    pass
