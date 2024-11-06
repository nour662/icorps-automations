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

def search_keyword(driver, keyword):
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="search"]'))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="usa-button ng-star-inserted"]'))
        )

        search_bar.send_keys(keyword)
        submit_button.click()
        sleep(5)

        # Get all links in the search results
        links = driver.find_elements(By.XPATH, '//div[@class="grid-row grid-gap"]//a')
        filtered_links = []

        # Only save links where the adjacent "R" text exists
        for link in links:
            try:
                # Find the text element near each link
                text_element = link.find_element(By.XPATH, './/following-sibling::td[@class="recipient-list__body-cell"]/span')
                if text_element.text == "R" or "C":
                    filtered_links.append(link.get_attribute('href'))
            except Exception:
                continue  # Skip if "R" text isn't found or there's an error

        return filtered_links[:5]

    except Exception as e:
        print(f"Error searching keyword '{keyword}': {e}")
        return []

# Scrapes the individual company pages for each company's information  
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

        legal_name = safe_find('//h1[@class="grid-col margin-top-3 display-none tablet:display-block wrap"]')
        num_uei = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[1]')
        cage = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[2]')
        physical_address = safe_find('//ul[@class="sds-list sds-list--unstyled margin-top-1"]')
        mailing_address = safe_find('(//ul[@class="sds-list sds-list--unstyled"])[2]')
        entity_url = safe_find_attr('//a[@class="usa-link"]', 'href')
        start_date = safe_find('//span[contains(text(), "Entity Start Date")]/following-sibling::span')
        contact1 = safe_find('(//div[@class="sds-card__body padding-2"]//child::h3)[1]')
        contact2 = safe_find('(//div[@class="sds-card__body padding-2"]//child::h3)[2]')
        state_country_incorporation = safe_find('(//div[@class= "grid-col-6 sds-field ng-star-inserted"])[3]//span[2]')
        congressional_district = safe_find('(//div[@class= "grid-col-6 sds-field"])[3]//span[2]')

        physical_address_lines = physical_address.split('\n') if physical_address else None
        mailing_address_lines = mailing_address.split('\n') if mailing_address else None

        result1 = ','.join(physical_address_lines) if physical_address_lines else None
        result2 = ','.join(mailing_address_lines) if mailing_address_lines else None

        # Returns and formats the results of the search which appear on the output .csv file 
        return {
            "keyword": keyword,
            "legal_name": legal_name,
            "num_uei": num_uei,
            "cage": cage,
            "physical_address": result1,
            "mailing_address": result2,
            "entity_url": entity_url,
            "start_date": start_date,
            "contact1": contact1,
            "contact2": contact2,
            "state_country_incorporation": state_country_incorporation,
            "congressional_district": congressional_district,
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Searches through the inputted .csv file and formats the company names 
def process_batch(driver, input_list, start, end):
    links = {}
    batch_input = input_list[start:end]

    # Universalizes the naming conventions of each company on the .csv file by removing company titles and symbols
    for name in batch_input:
        name = str(name)
        search_input = name.lower().strip()
        result_links = search_keyword(driver, search_input)
        links[name] = result_links

    links_data = []
    for keyword, urls in links.items():
        for url in urls:
            result = scrape_links(driver, keyword, url)
            if result:
                links_data.append(result)

    return links_data

# Main function to run the entire process
def main(starting_batch=0):
    input_df = pd.read_csv("input.csv") 
    input_list = input_df["UEI"].tolist()

    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://www.usaspending.gov/recipient")
        sleep(5)

        batch_size = 20
        num_batches = math.ceil(len(input_list) / batch_size)

        if not os.path.exists("company_output"):
            os.makedirs("company_output")

        for i in range(starting_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            batch_data = process_batch(driver, input_list, start_idx, end_idx)
            output_df = pd.DataFrame(batch_data)

            # Save each batch to a CSV file
            output_filename = f"company_output/batch_{i+1}.csv"
            output_df.to_csv(output_filename, index=False)
            print(f"Batch {i+1} completed and saved to '{output_filename}'")

            # Return to search page for the next batch
            driver.get("https://sam.gov/search/?index=ei&page=1&pageSize=25&sort=-relevance&sfm%5BsimpleSearch%5D%5BkeywordRadio%5D=ALL&sfm%5BsimpleSearch%5D%5BkeywordEditorTextarea%5D=&sfm%5Bstatus%5D%5Bis_active%5D=true&sfm%5Bstatus%5D%5Bis_inactive%5D=false")
            sleep(5)

    finally:
        driver.quit()

if __name__ == "__main__":
    starting_batch = int(input("Enter the batch number to start from: "))
    main(starting_batch)
