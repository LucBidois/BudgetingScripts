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
from dateutil.relativedelta import relativedelta
from enum import Enum
from gspread import Client, Spreadsheet, Worksheet
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
                       google_creds: str=mySecrets.google_account_creds_location) -> Worksheet:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(google_creds, scope)
        client = gspread.authorize(creds)
        return client.open(worksheet_name).worksheet(worksheet_page_name)

    def getGoogleClient(self, google_creds: str=mySecrets.google_account_creds_location) -> Client:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(google_creds, scope)
        return gspread.authorize(creds)

    def openSpreadsheet(self, client: Client, worksheet_name: str) -> Spreadsheet:
        return client.open(worksheet_name)

    def openWorksheetPage(self, client: Client, worksheet_name: str, page_name: str) -> Worksheet:
        return client.open(worksheet_name).worksheet(page_name)

    def readWorksheet(self, worksheet: Worksheet, range: str) -> list[list]:
        return worksheet.get(range)
    
    def debugPrintSpreadsheetValues(self, input):
        for i in input:
            print(i)


class PaySlipSheetUtils():
    """
    Class holding methods and attributs only used by my pay and rota tracking spreadsheet
    """
    g_utils: GoogleSpreadSheetUtils = GoogleSpreadSheetUtils()
    client: Client                  = g_utils.getGoogleClient()
    spreadsheet: Spreadsheet        = g_utils.openSpreadsheet(client, mySecrets.google_income_worksheet_name)

    def getWorksheet(self, page_name: str, range: str) -> {list[list], Worksheet}:
        worksheet_class = self.spreadsheet.worksheet(page_name)
        return self.g_utils.readWorksheet(worksheet_class, range), worksheet_class
    
    def prepareUpdateScheduledHours(self, worksheet:list, scraped_scheduled_data: dict[int, dict[int, dict[str, str]]]):
        sheet_values_A_to_E = []
        sheet_values_H_to_L = []
        sheet_values_new_rows = []
        new_row = 0
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
                        new_row = last_editable_row
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
                    first_row = row_num + 1
                else: 
                    row_num -= 1
                
                if date_exists and row_num:
                    sheet_values.append(self.rowValues(row_num + 1, date_str, week_day, time_clocked_in=start_time, time_clocked_out=end_time, holiday=holiday)[5:12])

        if date_exists and row_num:
            edit_range = f'F{row_num + 1}:L{first_row + 1}'
            return sheet_values[::-1], edit_range

    def updateWorksheet(self, worksheet: Worksheet, sheet_values: list[list], edit_range: str):
        worksheet.update(sheet_values, edit_range, value_input_option = ValueInputOption.user_entered )


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

    def payExpectationsRowValues(self, month_period: str, row: int, range_start_for_month: str, range_end_for_month: str, payslip: dict) -> list:
        return [
            month_period, # period (Month YY)
            "108.33", # basic units (contract 25 hours per week)
            f"=D{row-1}-B{row-1}", # Last Month Adjustment
            f"=SUM('{mySecrets.google_income_page_2_name}'!H{range_end_for_month}:H{range_start_for_month})", # Total worked hours. ex "H53:H83"
            f"=SUM('{mySecrets.google_income_page_2_name}'!I{range_end_for_month}:I{range_start_for_month}) * 0.2", # Night hours
            f"=SUM('{mySecrets.google_income_page_2_name}'!J{range_end_for_month}:J{range_start_for_month}) * 5 * O{row}", # Holiday Pay
            f"=B{row}*O{row}+C{row}*O{row-1}+E{row-1}*O{row-1}+F{row-1}", # Total
            '', # Pension adjustment
            '', # Deductions 
            f"=K{row-1}-B{row-1}", # Scheduled adjustment for last month 
            f"=SUM('{mySecrets.google_income_page_2_name}'!E{range_end_for_month}:E{range_start_for_month})", # Scheduled hours
            f"=SUM('{mySecrets.google_income_page_2_name}'!L{range_end_for_month}:L{range_start_for_month}) * 0.2", # total scheduled night hours 
            f"=SUM('{mySecrets.google_income_page_2_name}'!J{range_end_for_month}:J{range_start_for_month}) * 5 * O{row}", # total scheduled Holiday Pay
            f"=O{row} * (B{row}) + O{row-1} * (J{row} + L{row-1}) + M{row-1}", # Total from schedule
            "13.02", # Pay rate for month 
            payslip['salary'], # Gross Salary (Currently changed to 13.02 per hour)
            payslip['pension_AE'], # Pension AE
            payslip['deductions'], # Deductions 
            payslip['net_salary'], # Net Salary 
            '', # ''
            f"=P{row}-G{row}" # Expected vs actual
            ] 

    def findDateRowIndex(self, worksheet: list, date: str=datetime.datetime.today().strftime("%d/%m/%y")):

        for row in range(len(worksheet)):
            if worksheet[row][0] == date:
                return True, row

        print(f"Row not found for date {date}")
        return False, None
    
    def getFirstAndLastRow(self, worksheet: list, month: datetime.date):
        first_row = 0
        last_row = 0

        start_date = month.replace(day=1)
        end_date = month + relativedelta(months=1, days=-1)

        for i in range(len(worksheet)):
            row_num = i+1
            if worksheet[i][0] == "Date":
                continue

            if first_row and last_row:
                return first_row, last_row
            
            if datetime.datetime.strptime(worksheet[i][0], "%d/%m/%y").date() == start_date:
                first_row = row_num
            elif datetime.datetime.strptime(worksheet[i][0], "%d/%m/%y").date() == end_date:
                last_row = row_num

    def updatePayExpectations(self, payslip_data): # TODO: no update is taking place
        # payslip_data needs to be a list of the information for each month we plan on editing. 
        null_payslip = {}

        payslip_worksheet_list, payslip_worksheet = self.getWorksheet(page_name=mySecrets.google_income_page_1_name, range="A1:U")
        rota_worksheet_list, rota_worksheet = self.getWorksheet(page_name=mySecrets.google_income_page_2_name, range="A1:L")

        this_month = datetime.date.today().replace(day=1)
        next_month = this_month + relativedelta(months=1)
        last_month = this_month - relativedelta(months=1)
        compare_month = datetime.datetime.strptime(payslip_worksheet_list[-1][0], '%B %y').date().replace(day=1)

        # for rows that exist, update values
        for i in range(len(payslip_worksheet_list)):
            
            row_num = i+1 

            # skip headers row
            if payslip_worksheet_list[i][0] == "Period":
                continue

            # print(i)
            # print(payslip_worksheet_list[i])
            compare_month = datetime.datetime.strptime(payslip_worksheet_list[i][0], '%B %y').date().replace(day=1)


            print(compare_month)
            # only update bottom of the table
            # if (compare_month == this_month) or (compare_month == next_month) or (compare_month == last_month):
            if (compare_month == this_month):
                start_row, end_row = self.getFirstAndLastRow(rota_worksheet_list, compare_month)
                self.updatePayslipDetailsForRow(payslip_worksheet, compare_month, start_row, end_row, row_num, payslip_data)

        # if datetime.datetime.strptime(payslip_worksheet_list[-1][0], '%B %y').date().replace(day=1) != next_month: 
        #     month_period = datetime.datetime.strftime(next_month, '%B %y')
        #     row = len(payslip_worksheet_list)
        #     start_row, end_row = self.getFirstAndLastRow(rota_worksheet_list, compare_month)

        #     new_row_values = self.payExpectationsRowValues(month_period, row, start_row, end_row, payslip = payslip_data)
        #     payslip_worksheet.insert_rows(values=[new_row_values], row=row, value_input_option=ValueInputOption.user_entered)
        #        if no next month, add new row 
        

    def updatePayslipDetailsForRow(self, worksheet, month, start_row, end_row, edit_row, payslip_data = {'salary':'','pension_AE': '','deductions': '','net_salary': '' }):
        month_period = datetime.datetime.strftime(month, '%B %y')
        new_row = self.payExpectationsRowValues(month_period, edit_row, start_row, end_row, payslip_data)
        self.updateWorksheet(worksheet, [new_row], f"A{edit_row}")


    # def test(self):
    #     self.updatePayExpectations()

        # for row in worksheet_list:
        #     # skip first row 
        #     if row[0] == 'Period':
        #         continue

            # row[0] # month
        
            # which month is it,
            # find first and last date value from worked hours worksheet. 
            # grab payslip data. {'salary': '','pension': '','deductions': '','net_salary': ''}
            # payExpectationsRowValues(row[0], row.index, range_start_for_month, range_end_for_month, payslip)


        
        
        # get rota worksheet
        # get monthly income breakdown worksheet
        # for each month in the monthly income breakdown, we want to insert the predition of pay information.  

        # at the end of each month, we want to add the real payslip information. 
        # - we need a way to check which payslips are available 
        # - selenium navigation 
        # - beautiful soup grabbing relevant information. 
        

        # worksheet_values, sheet = self.getWorksheet(mySecrets.google_income_worksheet_name, mySecrets.google_income_page_2_name)
        # print(sheet)
        # values = [['testing', '', '', '', '', '', '', '', '', '', 'testing2'], ['testing3', '', '', '', '', '', 'hello', '', '', '', 'testing4']]
        # sheet.batch_update()
        # sheet.values_append(range = 'Worked hours - day!A6:L6', params = {'valueInputOption': 'USER_ENTERED', 'insertDataOption' : 'INSERT_ROWS'}, body = {'values': values}) # this has updated at the bottom...
        # worksheet.append_rows() # this will also only add rows at the end of the table. 
        # worksheet.insert_cols(values= values, col = 6, value_input_option= ValueInputOption.user_entered)
        # worksheet.insert_rows(values= values, row = 6, value_input_option= ValueInputOption.user_entered)


class BudgetingSheetUtils():
    pass
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
    payslip = PaySlipSheetUtils()
    payslip.test()
    pass
