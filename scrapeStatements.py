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
        self.scrapePdf(file_path)



    def scrapePdf(self, file_path):
        doc = pymupdf.open(file_path)
        page = doc[2]

        top_of_table = page.search_for("Type")[0].y1  # "STATEMENT OPENING BALANCE"
        bottom_of_table = page.search_for("STATEMENT CLOSING BALANCE")[0].y0

        table = ParseTab(page, pymupdf.Rect(0, top_of_table, page.rect.width, bottom_of_table))
        
        starting_balance = None
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
        
        return table_data

if __name__ == "__main__":
    scraper = ScrapeStatements()
    table_data = scraper.scrapeJointAccountPdf(month = "Aug-25")
    print(table_data)
