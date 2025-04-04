from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math, pandas as pd, sys, pickle, logging
from argparse import ArgumentParser
from time import sleep

'''
**Nour Ali Ahmed**
**Scott Lucarelli**
'''

## Fix the entity information filter selection
        

def search_keyword(driver, keyword):
    inactive = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Inactive")]'))
    )
    
    if not inactive.is_selected():
        inactive.click()
        
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="search"]'))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="usa-button ng-star-inserted"]'))
        )

        search_bar.send_keys(keyword)
        submit_button.click()

    
        links = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="grid-row grid-gap"]//a')))
         
        
        return [a.get_attribute('href') for a in links][:10]
    
    except Exception as e:
        logging.error(f"Error searching keyword {keyword}: {e}")  
        return []

def scrape_links(driver, keyword, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@class="sds-navbar__title"]')))

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
        contacts = safe_find('//div[@class="sds-card__body padding-2"]//child::h3')
        state_country_incorporation = safe_find('(//div[@class= "grid-col-6 sds-field ng-star-inserted"])[3]//span[2]')
        congressional_district = safe_find('(//div[@class= "grid-col-6 sds-field"])[3]//span[2]')

        physical_address_lines = physical_address.split('\n') if physical_address else None
        mailing_address_lines = mailing_address.split('\n') if mailing_address else None

        result1 = ','.join(physical_address_lines) if physical_address_lines else None
        result2 = ','.join(mailing_address_lines) if mailing_address_lines else None

        logging.info(f"Scraped data for {keyword}: {legal_name}, {num_uei}, {cage}, {physical_address}, {mailing_address}, {entity_url}")

        return {
            "keyword": keyword,
            "legal_name": legal_name,
            "num_uei": num_uei,
            "cage": cage,
            "physical_address": result1,
            "mailing_address": result2,
            "entity_url": entity_url,
            "start_date": start_date,
            "contacts": contacts,
            "state_country_incorporation": state_country_incorporation,
            "congressional_district": congressional_district,
        }

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}") 
        return None

def process_batch(driver, input_list, start, end):
        
    links = {}
    batch_input = input_list[start:end]

    for name in batch_input:
        name = str(name)
        search_input = name.lower().strip()
        search_input = search_input.replace(".", "").replace(",", "").replace("inc", "").replace("llc", "").replace("corp", "").replace("ltd", "").replace("limited", "").replace("pty", "")
        result_links = search_keyword(driver, search_input)
        links[name] = result_links

    links_data = []
    for keyword, urls in links.items():
        for url in urls:
            result = scrape_links(driver, keyword, url)
            if result:
                links_data.append(result)

    return links_data


def select_filters(driver): 
        
    search_button = WebDriverWait(driver , 10).until(
        EC.element_to_be_clickable((By.XPATH , '//a[@id = "search"]'))
    )

    search_button.click()


    entity_domain = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@aria-describedby="mat-mdc-chip-9-aria-description"]'))
    )
    entity_domain.click()


def load_cookies(driver, input_path):
    with open(input_path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    logging.info(f"Cookies loaded from {input_path}") 

def main(input_file, starting_batch, output_path):
    logging.basicConfig(filename=f'{output_path}/log/sam_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    starting_batch = int(starting_batch)

    input_df = pd.read_csv(input_file)
    input_df = input_df[(input_df['Entrepreneur Stage'] != 'Inactive')]
    input_df = input_df[(input_df['UEI'] != '')]
    input_list = input_df["Company"].drop_duplicates().tolist()
    
    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://sam.gov/")
        
        load_cookies(driver, "sam/cookies.pkl") # this cookies files causes an infinite loop where the program goes back and forth from the home/search page till timeout


        #sleep(500000)
        #driver.get("https://sam.gov/search/")

        select_filters(driver)

        batch_size = 10
        num_batches = math.ceil(len(input_list) / batch_size)

        for i in range(starting_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            logging.info(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            batch_data = process_batch(driver, input_list, start_idx, end_idx)

            output_df = pd.DataFrame(batch_data)

            output_filename = f"{output_path}/sam_batches/batch_{i+1}.csv"
            output_df.to_csv(output_filename, index=False)
            logging.info(f"Batch {i+1} completed and saved to {output_filename}")
            
            #reset to homepage for new batch
            driver.get("https://sam.gov/")
            select_filters(driver)
            

    finally:
        driver.quit()
        logging.info("Driver quit and process finished.") 

def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--starting_batch", "-s", required=False, help="Starting Batch")
    parser.add_argument("--input_file", "-i", required=True, help="Input File")
    parser.add_argument("--output_path", "-o", required=True, help = "Output Path")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.input_file, args.starting_batch, args.output_path)
