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

def scrape_links(driver, keyword, url):
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

def main(input_file='temp.csv', start_batch=0):
    if __name__ == "__main__":
        starting_batch = int(input("Enter the batch number to start from: "))
    if not input_file:
        print("Input file not provided.")
        return
    if not input_file.endswith('.csv'):
        print("Input file must be a CSV file.")
    if not input_file:
        print("Input file not provided.")
        return
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    input_df = pd.read_csv(input_file)
    print(input_df)

    input_df = input_df[input_df["UEI"].isnull()]
    print(input_df)

    input_list = input_df['DUNS Number'].tolist()

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
    main('temp.csv', starting_batch)
