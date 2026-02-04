import datetime
from tkinter import *
from tkinter import ttk
import scrapeRotaDetails
import googleSheet
from dateutil.relativedelta import relativedelta
from scrapeStatements import ScrapeStatements, BankSeleniumUtils

def main():

    root = Tk()
    root.title("Finances App")

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(mainframe, text="Welcome to the Finances App!").grid(column=1, row=1, sticky=W)
    ttk.Button(mainframe, text="Quit", command=root.destroy).grid(column=1, row=2, sticky=W)
    ttk.Button(mainframe, text="Update rota", command=updateRota).grid(column=2, row=2, sticky=W)
    ttk.Button(mainframe, text="Update Payslip info", command=updatePayslips).grid(column=3, row=2, sticky=W)
    ttk.Button(mainframe, text="Update expenses", command=updateExpenses).grid(column=4, row=2, sticky=W)

    root.mainloop()

def updateRota():
    scrapeRotaDetails.main()

def updatePayslips():
    data = scrapeRotaDetails.findAndScrapePayslipData()
    
    if not data:
        print("No payslip data found")
        return

    this_month = datetime.date.today().replace(day=1)
    last_month = this_month - relativedelta(months=1)
    next_month = this_month + relativedelta(months=1)

    try:
        payslip_utils = googleSheet.PaySlipSheetUtils()
        payslip_utils.updatePayExpectations(data['this_month'], this_month)
        payslip_utils.updatePayExpectations(data['last_month'], last_month)
        payslip_utils.updatePayExpectations(data['next_month'], next_month)
    except Exception as e: 
        print(f"Error updating payslip data: {e}")
        return
    
    print("Payslip data has been updated.")

def updateExpenses():
    scrape_utils = ScrapeStatements()
    scraped_data = scrape_utils.scrapeExpenses()
    budgetUtils = googleSheet.BudgetingSheetUtils()
    budgetUtils.UpdateExpenses(scraped_data)

    pass

def checkMonthlyRoutines():
    """I want these routines to check that my regualr monthly bills have 1. been processed, 2 are the right amount."""
    # utilities()
    # CouncilTax()
    # YearlyRoutines()
    # car insurance
    # water bill
    # mortgage
    pass

def searchJobBoards():
    pass

if __name__ == "__main__":
    main()