from pydoc import doc
import re
import time

import fitz
import matplotlib
import pandas
import numpy

import seleniumUtils
import mySecrets
from selenium.webdriver.common.by import By
import pymupdf ## issue, does not deal with empty cells in tables well. 


from operator import itemgetter
from itertools import groupby
import fitz


# ==============================================================================
# Function ParseTab - parse a document table into a Python list of lists
# ==============================================================================
def ParseTab(page, bbox, columns=None):
    """Returns the parsed table of a page in a PDF / (open) XPS / EPUB document.
    Parameters:
    page: fitz.Page object
    bbox: containing rectangle, list of numbers [xmin, ymin, xmax, ymax]
    columns: optional list of column coordinates. If None, columns are generated
    Returns the parsed table as a list of lists of strings.
    The number of rows is determined automatically
    from parsing the specified rectangle.
    """
    tab_rect = fitz.Rect(bbox).irect
    xmin, ymin, xmax, ymax = tuple(tab_rect)

    if tab_rect.is_empty or tab_rect.is_infinite:
        print("Warning: incorrect rectangle coordinates!")
        return []

    if type(columns) is not list or columns == []:
        coltab = [tab_rect.x0, tab_rect.x1]
    else:
        coltab = sorted(columns)

    if xmin < min(coltab):
        coltab.insert(0, xmin)
    if xmax > coltab[-1]:
        coltab.append(xmax)

    words = page.get_text("words")

    if words == []:
        print("Warning: page contains no text")
        return []

    alltxt = []

    # get words contained in table rectangle and distribute them into columns
    for w in words:
        ir = fitz.Rect(w[:4]).irect  # word rectangle
        if ir in tab_rect:
            cnr = 0  # column index
            for i in range(1, len(coltab)):  # loop over column coordinates
                if ir.x0 < coltab[i]:  # word start left of column border
                    cnr = i - 1
                    break
            alltxt.append([ir.x0, ir.y0, ir.x1, cnr, w[4]])

    if alltxt == []:
        print("Warning: no text found in rectangle!")
        return []

    alltxt.sort(key=itemgetter(1))  # sort words vertically

    # create the table / matrix
    spantab = []  # the output matrix

    for y, zeile in groupby(alltxt, itemgetter(1)):
        schema = [""] * (len(coltab) - 1)
        for c, words in groupby(zeile, itemgetter(3)):
            entry = " ".join([w[4] for w in words])
            schema[c] = entry
        spantab.append(schema)

    return spantab


class ScrapeStatements():

    def scrapeExpenses(self):
        pass
    
    def scrapeCreditCard(self, month):
        # Option 1 scrape pdfs, 
        # Option 2 scrape website
        pass

    def scrapeJointAccount(self, month):
        BankSeleniumUtils().navigateToBankWebsite() 
        # NOTE: this often results in an error on the side of the bank possibly, they are able to detect the automation.

    def scrapeCreditCardPdf(self, month):

        doc = pymupdf.open("bank_statements/Statement_3668_Aug-25.pdf")
        page = doc[2]

        top_of_table = page.search_for("Your Transactions")[0].y1
        bottom_of_table = page.search_for("STATEMENT CLOSING BALANCE")[0].y0

        print(top_of_table, bottom_of_table)

        table = ParseTab(page, pymupdf.Rect(0, top_of_table, page.rect.width, bottom_of_table))

        for t in table:
            # match rows with dates (discards new lines in descriptions)
            if re.match(r'\d\d \w{3} \d\d', t[0]):
                split = re.split(r' ', t[0])
                date = " ".join(split[0:3])
                description = " ".join(split[4:-2])
                print(date, description, split[-2], split[-1])

    def scrapeJointAccountPdf(self, month):
        pass

class BankSeleniumUtils():
    
    def navigateToBankWebsite(self):
        driver = seleniumUtils.setUpforSelenium()

        logged_in = self.logIntoWebsite(driver, mySecrets.my_bank_url, mySecrets.my_bank_userid, mySecrets.my_bank_password)
        if not logged_in:
            print("Failed to log in to bank website")
            return None
        
        # character 1 "/html/body/div/div[2]/div/div[1]/div/div/form/fieldset/div/div/div[1]"  # /label to know which letter # select for the character choice
        # character 2 "/html/body/div/div[2]/div/div[1]/div/div/form/fieldset/div/div/div[2]"

    def logIntoWebsite(self, driver, url, userID, password) -> bool:
        driver.get(url)
        time.sleep(2)

        # id: frmLogin:strCustomerLogin_userID
        # id: frmLogin:strCustomerLogin_pwd
        try: 
            self.fillLoginDetails(driver, userID, password)
            self.fillMemorableInfo(driver)
        except:
            return False

        return True 
    
    def fillLoginDetails(self, driver, userID, password):
        driver.find_element(By.ID, "frmLogin:strCustomerLogin_userID").send_keys(userID)
        time.sleep(1)
        driver.find_element(By.ID, "frmLogin:strCustomerLogin_pwd").send_keys(password)
        time.sleep(1)
        driver.find_element(By.ID, "frmLogin:btnLogin1").click()
        time.sleep(5) # wait for page to load
    
    def fillMemorableInfo(self, driver):
        char1 = driver.find_element(By.XPATH, value="/html/body/div/div[2]/div/div[1]/div/div/form/fieldset/div/div/div[1]/label").text
        char2 = driver.find_element(By.XPATH, value="/html/body/div/div[2]/div/div[1]/div/div/form/fieldset/div/div/div[2]/label").text
        char3 = driver.find_element(By.XPATH, value="/html/body/div/div[2]/div/div[1]/div/div/form/fieldset/div/div/div[3]/label").text

        char1 = char1[9:-2]
        char2 = char2[9:-2]
        char3 = char3[9:-2]
        print(f"Characters requested: {char1}, {char2}, {char3}")

        driver.find_element(By.ID, value="frmentermemorableinformation1:strEnterMemorableInformation_memInfo1").send_keys(mySecrets.my_bank_memorable_information[int(char1)-1])
        time.sleep(1) 
        driver.find_element(By.ID, value="frmentermemorableinformation1:strEnterMemorableInformation_memInfo2").send_keys(mySecrets.my_bank_memorable_information[int(char2)-1])
        time.sleep(1) 
        driver.find_element(By.ID, value="frmentermemorableinformation1:strEnterMemorableInformation_memInfo3").send_keys(mySecrets.my_bank_memorable_information[int(char3)-1])
        time.sleep(1) 

        driver.find_element(By.ID, value="frmentermemorableinformation1:btnContinue").click()
        # time.sleep(5) # wait for page to load

if __name__ == "__main__":
    scraper = ScrapeStatements()
    # scraper.scrapeJointAccountPdf("month")
    scraper.scrapeCreditCardPdf("month")