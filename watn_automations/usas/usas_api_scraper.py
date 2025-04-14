import requests
import pandas as pd
from time import sleep
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import math
import csv
import tempfile, json


def main():
    input_file = "watn_automations\\usas\\small_uei.csv"
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    input_df = pd.read_csv(input_file)
    if 'num_uei' not in input_df.columns:
        print("The CSV must contain a 'UEI' column.")
        return

    input_list = input_df['num_uei'].tolist()

    # # Configure Chrome WebDriver options
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--remote-debugging-port=9230")

    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    # API stuff I guess :)
    base_url = "https://api.usaspending.gov"
    search_endpoint = "/api/v2/recipient/recipient_search_text/"
    award_search_endpoint = "/api/v2/search/spending_by_award/"
    
    # define the input filters we want and the output data tags we want
    setup =  {"filters": {
        "recipient_search_text":['LA9LCVM7HMK5'],
        "award_type_codes": ["A", "B" , "C" , "D", "02", "03", "04", "05"]
      },
      "fields": ["Recipient Name", "Start Date",
          "End Date",
          "Award Amount",
          "Awarding Agency",
          "Awarding Sub Agency",
          "Contract Award Type",
          "Award Type",
          "Funding Agency",
          "Funding Sub Agency"]
    }

    response = requests.get(base_url + award_search_endpoint, json=setup)

    if response.status_code == 200:
        data = response.json()
    
        temp_file = tempfile.NamedTemporaryFile(mode = 'w+t', suffix = '.json', delete=True)
        try:
            json.dump(data, temp_file)
            temp_filename = temp_file.name
        except Exception:
            temp_file.close()
            raise
        
            
    # need to read UEI's from input csv
    def uei_list (file_path):
        with open (file_path, mode = 'r') as file:
            reader = csv.DictReader(file)
            return [row["UEI"].strip() for row in reader if row["UEI"].strip()] 
            # list is going to be unfriendly, write the loop and append "carter will do this"

    #search recipient and award data
    def get_data (uei):
        response = requests.post( # find uei
            base_url + award_search_endpoint,
            json = {"text":uei} #put uei into csv, with column uei
        )
        
    # response.raise_for_status
    # data = response.json()
    # if not data["results"] :
    #     return None
    # return data["results"][0]

        
if __name__ == "__main__":
    main()
