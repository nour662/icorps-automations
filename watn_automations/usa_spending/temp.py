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
import shutil

# Function to search for keywords and get links where adjacent text is "R"
def search_keyword(driver, keyword):
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@class="search-section__input"]'))
        )

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="search-section__button"]'))
        )

        search_bar.send_keys(keyword)
        submit_button.click()
        sleep(7)

        links = driver.find_elements(By.XPATH, '//td[@class="recipient-list__body-cell"][span[text()="R"]]/a')

        filtered_links = [link.get_attribute('href') for link in links]

        return filtered_links


    except Exception as e:
        print(f"Error searching keyword '{keyword}': {e}")
        return []

# Function to scrape data for each company link
def scrape_links(driver, keyword, url):
    try:
        driver.get(url)
        sleep(5)

        def safe_find(xpath):
            try:
                return driver.find_element(By.XPATH, xpath).text
            except Exception:
                return None

        def safe_find_attr(xpath, attr):
            try:
                return driver.find_element(By.XPATH, xpath).get_attribute(attr)
            except Exception:
                return None

        legal_name = safe_find('//h2[@class="recipient-overview__title"]')
        num_uei = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[1]')
        cage = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[2]')

        address_divs = driver.find_elements(By.XPATH, '//tr[th[contains(text(), "Address")]]/td/div')
        full_address = ', '.join(div.text.strip() for div in address_divs if div.text.strip())
        congressional_district = safe_find('//th[div[contains(text(), "Congressional District")]]/following-sibling::td/div')

        # Separate dictionary for company info
        company_info = {
            "keyword": keyword,
            "legal_name": legal_name,
            "num_uei": num_uei,
            "cage": cage,
            "full_address": full_address, 
            "congressional_district": congressional_district,
        }
        print(company_info)

        return company_info

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Function to get funding info
def get_funding_info(driver, keyword, output_folder):
    try:
        # Navigate to the awards page
        awards_url = "/search"  # Adjust this if the URL needs to be constructed differently
        driver.get("https://www.usaspending.gov" + awards_url)
        sleep(5)

        # Click the download button to bring up the pop-up
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="usda-button" and @title="Download"]'))
        )
        download_button.click()
        sleep(5)  # Allow time for the folder to download

        # Click the "Award" button on the pop-up
        award_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="level-button" and @title="Award"]'))
        )
        award_button.click()
        sleep(1)

        # Click the "Everything" button
        everything_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="level-button" and @title="Everything"]'))
        )
        everything_button.click()
        sleep(2)  # Wait for a bit for any potential load

        # Move the downloaded folder from Downloads to the funding output folder
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        funding_folder = os.path.join(os.getcwd(), output_folder)

        # Assuming the folder is named based on the keyword or a pattern; adjust if needed
        folder_name = f"{keyword}_awards"  # Change this to match the expected folder name
        source_path = os.path.join(downloads_folder, folder_name)
        destination_path = os.path.join(funding_folder, folder_name)

        if os.path.exists(source_path):
            if not os.path.exists(funding_folder):
                os.makedirs(funding_folder)

            shutil.move(source_path, destination_path)
            print(f"Moved '{source_path}' to '{destination_path}'")
        else:
            print(f"Source folder '{source_path}' does not exist.")

    except Exception as e:
        print(f"Error getting funding info for '{keyword}': {e}")

# Processes each batch of company names and returns separate lists for company data
def process_batch(driver, input_list, start, end, funding_output_folder):
    company_data = []
    
    batch_input = input_list[start:end]

    for name in batch_input:
        search_input = str(name)
        #search_input = name.lower().strip().replace(".", "").replace(",", "").replace("inc", "").replace("llc", "").replace("corp", "").replace("ltd", "").replace("limited", "").replace("pty", "")
        result_links = search_keyword(driver, search_input)
        
        for url in result_links:
            company_info = scrape_links(driver, search_input, url)
            if company_info:
                company_data.append(company_info)
                get_funding_info(driver, search_input, funding_output_folder)  # Get funding info after scraping company info

    return company_data

# Main function to process and save batches to company CSV
def main(starting_batch=0):
    ##input_df = pd.read_csv("input.csv")
    ##input_list = input_df["UEI"].tolist()
    input_list = ['JJTZLGTS4W36']

    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    funding_output_folder = "funding_output"  # Specify the output folder for funding info

    try:
        driver.get("https://www.usaspending.gov/recipient")
        sleep(5)

        batch_size = 20
        num_batches = math.ceil(len(input_list) / batch_size)

        if not os.path.exists("company_output"):
            os.makedirs("company_output")

        if not os.path.exists(funding_output_folder):
            os.makedirs(funding_output_folder)

        for i in range(starting_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            company_data = process_batch(driver, input_list, start_idx, end_idx, funding_output_folder)

            company_df = pd.DataFrame(company_data)

            # Save each batch to CSV files
            company_filename = f"company_output/company_batch_{i+1}.csv"
            company_df.to_csv(company_filename, index=False)

            print(f"Batch {i+1} completed and saved to '{company_filename}'")

        driver.get("https://www.usaspending.gov/recipient")

    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    starting_batch = int(input("Enter the batch number to start from: "))
    main(starting_batch)