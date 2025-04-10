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

# This function accesses the USA Spending website and searches for a given keyword (UEI).
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
        sleep(2)  # Wait for the results to load

        priority_classes = [
            "recipient-landing__icon recipient-landing__icon_recipient",
            "recipient-landing__icon recipient-landing__icon_child",
            "recipient-landing__icon recipient-landing__icon_parent"
        ]
        found_option = False
        
        for class_name in priority_classes:
            try:
                # Find the <span> that indicates this recipient type.
                span = driver.find_element(By.XPATH, f'//span[contains(@class, "{class_name}")]')
                
                # Move up to the <td> that contains this span
                td = span.find_element(By.XPATH, './ancestor::td')
                
                # Inside that <td>, find the first <a> tag
                link = td.find_element(By.XPATH, './/a')
                
                # Click the link
                print(f"Clicking option with class: {class_name} - Link text: '{link.text}'")
                link.click()
                sleep(2)  # Wait for the page to load after clicking
                
                # Capture the resulting URL
                result_url = driver.current_url
                print(f"URL after clicking: {result_url}")
                result_links.append(result_url)
                
                found_option = True
                break  # Stop once we've successfully clicked a link
            except:
                # If we can't find a span or link with this class, move on to the next
                pass
        
        if not found_option:
            print(f"No matching recipient option found for keyword '{keyword}'.")
    
    except Exception as e:
        print(f"Error searching keyword '{keyword}': {e}")

# Locates the page of each company by UEI and extracts company information
def scrape_links(driver, keyword, url):
    """
    This function seeks to locate each company's legal name, UEI number, DUNS number, CAGE, full address, and
    congressional district. If it cannot locate the company's record, then it will be returned that there was an error 
    scraping that specific URL and UEI.
    """
    try:
        # Navigate to the company's page
        driver.get(url)

        # Helper function to safely find elements by XPath
        def safe_find(xpath):
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                return element.text
            except Exception:
                return None

        # Extract company details
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

        # Compile the extracted information into a dictionary
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
#
#
#def get_funding_info(): 
#    pass
#
#

def get_downloads(uei_list, driver):
    '''Populate all of the UEIs into the recipeient search then do a mass 
        download of all of the funds and award data.'''
    try: 
        driver.get('https://www.usaspending.gov/search')
        recipient_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label = "Recipient"]'))
        )
        # driver.execute_script("arguments[0].setAttribute('aria-pressed', 'true');", recipient_dropdown)
        recipient_dropdown.click()

        clear_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class= "clear-all__button"]'))
        )
        clear_filter.click()
        
        # Search and select all of the UEI filters
        try:
            for uei in uei_list: 
                input_field = driver.find_element(By.XPATH, '//input[@class= "geo-entity-dropdown__input"]')
                input_field.clear()
                input_field.send_keys(uei)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(@class, "checkbox-type-filter")]/div[1]'))
                )
                
                checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div/div[1]/div[1]/div[3]/div[7]/div[2]/div/div[3]/div/div[1]//input[@type="checkbox"]'))
                )     
                        
                driver.execute_script("arguments[0].click();", checkbox)
                
                # submit = WebDriverWait(driver, 10).until(
                #     EC.element_to_be_clickable((By.XPATH, ".button__md.button-type__primary-light.submit-button"))
                # )
                # submit.click()
        except Exception as e:
            print(f"Filter not Found: {e}")
        sleep(1000)
        
    except Exception as e:
        print(f"Page Setup Failed: {e}")

def process_batch(driver, input_list, start, end, batch_number):
    company_data = []
    batch_input = input_list[start:end]

    get_downloads(batch_input, driver)
    # for name in batch_input:
    #     result_links = []
    #     search_keyword(driver, name, result_links)

    #     # Remove duplicate links, if any
    #     result_links = list(set(result_links))
    #     print(f"Unique search results for {name}: {result_links}")  # Debug print

    #     for url in result_links:
    #         company_info = scrape_links(driver, name, url)
    #         if company_info:
    #             company_data.append(company_info)

    # # Save the batch results to a CSV file
    # company_df = pd.DataFrame(company_data).drop_duplicates()
    # company_filename = f"company_output/company_batch_{batch_number}.csv"
    # company_df.to_csv(company_filename, index=False)
    # print(f"Batch {batch_number} company data saved to '{company_filename}'")
    
# simple main
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

    try:
        batch_size = 5  # Number of UEIs to process per batch
        num_batches = math.ceil(len(input_list) / batch_size)

        # Create output directory if it doesn't exist
        if not os.path.exists("company_output"):
            os.makedirs("company_output")

        # Process each batch
        for i in range(1, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            process_batch(driver, input_list, start_idx, end_idx, i+1)
    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

'''
# Divides the input file into batches, reads it, and outputs results
def main(input_file='input.csv', start_batch=0):
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    input_df = pd.read_csv(input_file)
    if 'UEI' not in input_df.columns:
        print("The CSV must contain a 'UEI' column.")
        return

    input_list = input_df['UEI'].tolist()

    # Configure Chrome WebDriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9230")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        batch_size = 2  # Number of UEIs to process per batch
        num_batches = math.ceil(len(input_list) / batch_size)

        # Create output directory if it doesn't exist
        if not os.path.exists("company_output"):
            os.makedirs("company_output")

        # Process each batch
        for i in range(start_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            process_batch(driver, input_list, start_idx, end_idx, i+1)
    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        driver.quit()

# Entry point of the script
if __name__ == "__main__":
    starting_batch = int(input("Enter the batch number to start from: "))
    main('input.csv', starting_batch)
'''