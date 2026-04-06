from pydoc import doc
import re
from selenium.webdriver.common.by import By
import pymupdf ## issue, does not deal with empty cells in tables well. 
from ParseTab import ParseTab

class ScrapeStatements():

    def scrapeExpenses(self):
        pass
    
    def scrapeCreditCardPdf(self, month = "Aug-25"):

        file_path = f"bank_statements/Statement_7313_{month}.pdf"
        self.scrapePdf(file_path)

        # find pdfs to date, 
        # run scrapePdf for each month needed
        # return json of data for each month
        pass

    def scrapeJointAccountPdf(self, month):

        file_path = f"bank_statements/Statement_3668_{month}.pdf"
        return self.scrapePdf(file_path)

    def scrapeStatementPage(self, page, starting_balance = None, last_balance = None):

        if page.search_for("STATEMENT OPENING BALANCE"):
            print("first page")
            # TODO: need to handle first page differently to other pages - starting balance is not empty after first page.
            # maybe make starting balance a parameter in this fucntion, as the page is known before calling

        top_of_table = page.search_for("Type")[0].y1
        if page.search_for("STATEMENT CLOSING BALANCE"):
            bottom_of_table = page.search_for("STATEMENT CLOSING BALANCE")[0].y0
        else:
            bottom_of_table = page.search_for("Continued on next page")[0].y0

        table = ParseTab(page, pymupdf.Rect(0, top_of_table, page.rect.width, bottom_of_table))
        
        table_data = []
        for row in table:
            
            split = re.split(r' ', row[0])

            if re.match(r'\d\d \w{3} \d\d', " ".join(split[0:3])):
                
                try: 
                    current_balance = float(split[-1].replace(",", ""))
                except ValueError:
                    continue
                
                if starting_balance is None:
                    starting_balance = current_balance
                    last_balance = starting_balance
                    continue

                date = " ".join(split[0:3])
                description = " ".join(split[4:-2])

                inflow, outflow = 0, 0
                if last_balance < current_balance:
                    inflow = float(split[-2].replace(",", ""))
                else: 
                    outflow = float(split[-2].replace(",", ""))

                # print(date, description, outflow, inflow)
                last_balance = float(split[-1].replace(",", ""))
                table_data.append([date, description, outflow, inflow, current_balance])
        return starting_balance, last_balance, table_data

    def findFirstandLastPagetoScrape(self, doc):
        page = doc[2] # Always start at page 3
        for page in doc:
            if page.search_for("STATEMENT OPENING BALANCE"):
                first_page = page.number
                print(f"First page to scrape: {first_page}")
            if page.search_for("STATEMENT CLOSING BALANCE"): # or page.search_for("Continued on next page"):
                last_page = page.number
                print(f"Last page to scrape: {last_page}")
        return first_page, last_page

    def scrapePdf(self, file_path):
        doc = pymupdf.open(file_path)
        
        first_page, last_page = self.findFirstandLastPagetoScrape(doc)

        starting_balance = None
        last_balance = None
        statement_data = []
        for page_num in range(first_page, last_page + 1):
            starting_balance, last_balance, table_data = self.scrapeStatementPage(page=doc[page_num], starting_balance=starting_balance, last_balance=last_balance)
            statement_data.append(table_data)
        
        return statement_data

if __name__ == "__main__":
    scraper = ScrapeStatements()
    table_data = []
    table_data.append(scraper.scrapeJointAccountPdf(month = "Aug-25"))
    table_data.append(scraper.scrapeJointAccountPdf(month = "Sep-25"))
    table_data.append(scraper.scrapeJointAccountPdf(month = "Oct-25"))
    print(table_data)
