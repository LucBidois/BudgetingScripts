import requests
from bs4 import BeautifulSoup
import mySecrets

def main():

    URL = mySecrets.my_job_website_url
    print(f"Key : {mySecrets.my_job_website_url}")
    # page = requests.get(URL)

    # soup = BeautifulSoup(page.content, "html.parser")
    # # results = soup.find(id="ResultsContainer")

    enterEmail()
    enterPassword()
    clickLoginButton()

def enterEmail():
    pass

def enterPassword():
    pass    

def clickLoginButton():
    pass

if __name__ == "__main__":
    main()