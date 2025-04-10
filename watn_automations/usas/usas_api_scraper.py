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

    # Configure Chrome WebDriver options
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9230")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    # API stuff I guess :)
    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    

if __name__ == "__main__":
    main()
