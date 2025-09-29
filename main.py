from tkinter import *
from tkinter import ttk
import scrapeRotaDetails
import googleSheet

def main():

    root = Tk()
    root.title("Finances App")

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(mainframe, text="Welcome to the Finances App!").grid(column=1, row=1, sticky=W)
    ttk.Button(mainframe, text="Quit", command=root.destroy).grid(column=1, row=2, sticky=W)
    ttk.Button(mainframe, text="Update rota", command=updateRota()).grid(column=2, row=2, sticky=W)
    ttk.Button(mainframe, text="Update Payslip info", command=updatePayslips()).grid(column=3, row=2, sticky=W)
    ttk.Button(mainframe, text="Update expenses", command=updateExpenses()).grid(column=4, row=2, sticky=W)

    root.mainloop()

def updateRota():
    scrapeRotaDetails.main()

def updatePayslips():
    data = scrapeRotaDetails.findAndScrapePayslipData()

    payslip_utils = googleSheet.PaySlipSheetUtils()
    payslip_utils.updatePayExpectations(data)

def updateExpenses():
    pass

if __name__ == "__main__":
    main()