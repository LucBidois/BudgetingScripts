import time
import seleniumUtils
import mySecrets
from selenium.webdriver.common.by import By
import pymupdf

"""
camelot
tabula
pdf plumber
pdftables
pdfminer
"""

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
        out = open("output.txt", "wb") # create a text output
        for page in doc: # iterate the document pages
            # tables = page.find_tables()

            # for table in tables: 
            #     tableinfo = table.extract()
            #     print(tableinfo)
            text = page.get_text().encode("utf8") # get plain text (is in UTF-8)

            """
            new lines are used for each column
            I could find each new row by looking for the new date for each new transaction
            some Details fields are on more than one line. 
            On each new page I need to ignore the headers. 

            I can stop extracting when I reach the closing balance line. 

            Credit card and debit card have slight different formats. 
            """

            out.write(text) # write text of page
            out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
        out.close()

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
    scraper.scrapeCreditCardPdf("month")