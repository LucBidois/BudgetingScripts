# I will store the references to secrets here
# e.g. API keys, database passwords, etc.
from dotenv import load_dotenv
import os

load_dotenv("environmentVariables.env")

my_job_website_url = os.getenv("my_job_website_url")
my_job_email = os.getenv("my_job_email")
my_job_password = os.getenv("my_job_password")

my_bank_url = os.getenv("my_bank_url")
my_bank_email = os.getenv("my_bank_email")
my_bank_userid = os.getenv("my_bank_userid")
my_bank_password = os.getenv("my_bank_password")
my_bank_memorable_information = os.getenv("my_bank_memorable_information")

google_sheet_name = os.getenv("google_sheet_name")
google_account_creds_location = os.getenv("google_account_creds_location")