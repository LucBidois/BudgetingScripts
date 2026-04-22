from pydoc import doc
import re
from selenium.webdriver.common.by import By
import pymupdf
from ParseTab import ParseTab

class ScrapeStatements():

    def scrapeExpenses(self, filepath) -> list:
        scraped_data = []
        # TODO: check correct file using account number - check current account or credit card, or exit if wrong file selected
        scraped_data = self.scrapePdf(filepath)
        return scraped_data

    def scrapeCreditCardPdf(self, filepath) -> list:
        self.scrapePdf(filepath)

        # find pdfs to date, 
        # run scrapePdf for each month needed
        # return json of data for each month
        pass

    def scrapeStatementPage(self, page, starting_balance = None, last_balance = None) -> tuple[float, float, list]:
        # NOTE: detection is built around current account statements specifically

        top_of_table = page.search_for("Type")[0].y1 # detecting top of table using "pmnt type" in the header
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

                last_balance = float(split[-1].replace(",", ""))
                table_data.append([date, description, outflow, inflow, current_balance])
        return starting_balance, last_balance, table_data

    def findFirstandLastPagetoScrape(self, doc) -> tuple[int, int]:
        page = doc[2] # Always start at page 3
        for page in doc:
            if page.search_for("STATEMENT OPENING BALANCE"):
                first_page = page.number
            if page.search_for("STATEMENT CLOSING BALANCE"):
                last_page = page.number

        print(f"Scraping pages {first_page} to {last_page}")
        return first_page, last_page

    def scrapePdf(self, file_path) -> list:
        doc = pymupdf.open(file_path)
        
        first_page, last_page = self.findFirstandLastPagetoScrape(doc)

        starting_balance = None
        last_balance = None
        statement_data = []
        for page_num in range(first_page, last_page + 1):
            starting_balance, last_balance, table_data = self.scrapeStatementPage(page=doc[page_num], starting_balance=starting_balance, last_balance=last_balance)
            statement_data += table_data
        
        return statement_data


if __name__ == "__main__":
    pass
