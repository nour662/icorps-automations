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

"""
This script searches the USA Spending government database for companies of interest by UEI Number. It takes in input
from a .csv file named "input.csv". 

The output of this script comes in 2 groups: funding output and company output. 

1. Company Output: This script collects company information for each UEI entered into the program and outputs the 
results in batches. The format of the results is as follows:

keyword,legal_name,uei,legacy_duns,cage,full_address,congressional_district

2. Funding Output: This script will pull each companies documents off the USA spending website and merge all pulled 
documents together based on type. The names of the outputted merged .csv files are as follows:
    - assistance_prime_award.csv
    - assistance_sub_award.csv
    - contract_prime_award.csv
    - coontract_sub_award.csv

Because an unique identifier is used as a search term, cleaning of the data is not required 

**Nour Ali Ahmed**
"""

#This function acesses the USA Spending website
def search_keyword(driver, keyword, result_links):
    try:
        driver.get("https://www.usaspending.gov/recipient")
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@class="search-section__input"]'))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="search-section__button"]'))
        )
        search_bar.send_keys(keyword)
        submit_button.click()
        sleep(4)

        links = driver.find_elements(By.XPATH, '//td[@class="recipient-list__body-cell"]/a')
        filtered_links = [link.get_attribute('href') for link in links]

        result_links.extend(filtered_links)  # Extend the list instead of appending lists
    except Exception as e:
        print(f"Error searching keyword '{keyword}': {e}")

def get_downloads(uei_list):
    '''Populate all of the UEIs into the recipeient search then do a mass 
        download of all of the funds and award data.'''
#Locates the page of each company by UEI and extracts company information
def scrape_links(driver, keyword, url):
    """
    This function seeks to locate each company's  legal name, UEI number, DUNS number, CAGE, full address, and
    congressional district. If it cannot locate the company's record, then it will be returned that there was an error 
    scraping that specific URL and UEI.
    """
    try:
        driver.get(url)

        def safe_find(xpath):
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                return element.text
            except Exception:
                return None

        legal_name = safe_find('//h2[@class="recipient-overview__title"]')
        if legal_name:
            legal_name = legal_name.split('\n')[0].strip()

        identifiers = safe_find('//td[@class="recipient-section__details-table-first-td"]')
        uei, legacy_duns = identifiers.split("\n") if identifiers else (None, None)
        uei = uei.strip().replace(" (UEI )", "") if uei else None
        legacy_duns = legacy_duns.strip().replace(" (Legacy DUNS )", "") if legacy_duns else None

        cage = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[2]')
        address_divs = driver.find_elements(By.XPATH, '//tr[th[contains(text(), "Address")]]/td/div')
        full_address = ', '.join(div.text.strip() for div in address_divs if div.text.strip())

        congressional_district = safe_find('//th[div[contains(text(), "Congressional District")]]/following-sibling::td/div')

        company_info = {
            "keyword": keyword,
            "legal_name": legal_name,
            "uei": uei,
            "legacy_duns": legacy_duns,
            "cage": cage,
            "full_address": full_address,
            "congressional_district": congressional_district,
        }
        if uei == legacy_duns:
            legacy_duns = None

        return company_info
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

#
def process_batch(driver, input_list, start, end, batch_number):
    company_data = []
    batch_input = input_list[start:end]

    for name in batch_input:
        result_links = []
        search_keyword(driver, name, result_links)

        for url in result_links:
            company_info = scrape_links(driver, name, url)
            if company_info:
                company_data.append(company_info)

    company_df = pd.DataFrame(company_data)
    company_filename = f"company_output/company_batch_{batch_number}.csv"
    company_df.to_csv(company_filename, index=False)
    print(f"Batch {batch_number} company data saved to '{company_filename}'")

#Divides the input file into batches, reads it, and outputts results
def main(input_file='input.csv', start_batch=0):
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    input_df = pd.read_csv(input_file)
    if 'UEI' not in input_df.columns:
        print("The CSV must contain a 'UEI' column.")
        return

    input_list = input_df['UEI'].tolist()

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9230")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        batch_size = 2
        num_batches = math.ceil(len(input_list) / batch_size)

        if not os.path.exists("company_output"):
            os.makedirs("company_output")

        for i in range(start_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            process_batch(driver, input_list, start_idx, end_idx, i+1)
    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    starting_batch = int(input("Enter the batch number to start from: "))
    main('input.csv', starting_batch)
