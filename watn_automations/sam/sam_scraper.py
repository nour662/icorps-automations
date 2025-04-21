from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math, pandas as pd, sys, pickle, logging
from argparse import ArgumentParser
import re

"""
SAM.gov Scraper
This script automates the process of scraping data from the SAM.gov website using Selenium.
It searches for company names, collects URLs from the search results, and scrapes relevant data from each URL.
"""

def search_keyword(driver, keyword) -> list:
    """
    Searches for a keyword in the SAM.gov search bar and returns the first 10 URLs found.
    It waits for the search bar and submit button to be clickable, enters the keyword, and clicks the submit button.
    If the search is successful, it collects the URLs of the first 10 results.
    If any error occurs during the process, it logs the error and returns an empty list.

    Arguments:
        driver: selenium webdriver
        keyword: str, the keyword to search for

    Returns:
        list: a list of URLs found in the search results
    """
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="search"]'))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="usa-button ng-star-inserted"]'))
        )

        search_bar.clear()
        search_bar.send_keys(keyword)
        submit_button.click()

        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//h1[text()="No matches found"]'))
            )
            logging.info(f"No matches found for {keyword}")
            return []
        except Exception as e:
            pass  

        links = WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.XPATH, '//div[@class="grid-row grid-gap"]//a')
        )

        return [a.get_attribute('href') for a in links][:10]

    except Exception as e:
        logging.error(f"Error searching keyword {keyword}: {e}")
        return []

def scrape_links(driver, keyword, url) -> dict:
    """
    Scrapes the details from the given URL and returns a dictionary with the scraped data.
    This function waits for the page to load, then extracts various details such as legal name, UEI, CAGE, addresses, etc.
    It uses XPath to locate the elements on the page and handles exceptions if any element is not found.

    Arguments:
        driver: selenium webdriver
        keyword: str, the keyword used for the search
        url: str, the URL to scrape data from

    Returns:
        dict: a dictionary containing the scraped data
    """

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
                element = driver.find_elements(By.XPATH, xpath).get_attribute(attr)
                return element
            except Exception:
                return None
        def safe_find_contacts(xpath, attr):
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                return [element.get_attribute(attr) for element in elements]
            except Exception:
                return []

        def extract_names(contact_texts):
            if not contact_texts:
                return []
            pattern = r"^([A-Za-z]+)\s?([A-Za-z]?.)?\s([A-Za-z]+)"
            extracted_names = []
            for text in contact_texts:
                try:
                    match = re.match(pattern, text.strip())
                    if match:
                        first_name = match.group(1)
                        last_name = match.group(3)
                        full_name = f"{first_name.title()} {last_name.title()}" if first_name and last_name else None
                        if full_name:
                            extracted_names.append(full_name)
                except Exception as e:
                    logging.error(f"Error extracting names from text '{text}': {e}")
            return list(set(extracted_names))

        legal_name = safe_find('//h1[@class="grid-col margin-top-3 display-none tablet:display-block wrap"]')
        num_uei = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[1]')
        cage = safe_find('(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[2]')
        physical_address = safe_find('//ul[@class="sds-list sds-list--unstyled margin-top-1"]')
        mailing_address = safe_find('(//ul[@class="sds-list sds-list--unstyled"])[2]')
        entity_url = safe_find_attr('//a[@class="usa-link"]', 'href')
        start_date = safe_find('//span[contains(text(), "Entity Start Date")]/following-sibling::span')
        contacts_texts = safe_find_contacts('//div[@class="sds-card__body padding-2"]//child::h3', 'textContent')
        contacts = extract_names(contacts_texts)
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

def process_batch(driver, input_list, start, end) -> list:
    """
    Processes a batch of input names, searches for each name, and scrapes the details from the search results.
    This function takes a list of names, divides it into batches, and for each name in the batch, it performs a search and scrapes the details from the resulting URLs.
    It returns a list of dictionaries containing the scraped data.

    Arguments:
        driver: selenium webdriver
        input_list: list of names to search for
        start: int, starting index for the batch
        end: int, ending index for the batch

    Returns:
        list: a list of dictionaries containing the scraped data
    """

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

def select_filters(driver) -> None:
    """
    Selects filters on the SAM.gov website to narrow down the search results.
    This function waits for the search button and entity domain to be clickable, then clicks them.
    It also selects the inactive checkbox to include inactive companies in the search results.
    If any error occurs during the process, it logs the error and quits the driver.

    Arguments:
        driver: selenium webdriver
    """
    try:
        search_button = WebDriverWait(driver , 10).until(
            EC.element_to_be_clickable((By.XPATH , '//a[@id = "search"]'))
        )
        search_button.click()

        entity_domain = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@aria-describedby="mat-mdc-chip-9-aria-description"]'))
        )
        entity_domain.click()

        inactive_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//label[@class="usa-checkbox__label"]'))
        )

        inactive_checkbox.click()
        
    except Exception as e:
        logging.error(f"Error selecting filters: {e}")
        driver.quit()

def load_cookies(driver, input_path)-> None:
    """
    Loads cookies from a specified file and adds them to the Selenium WebDriver.
    This function uses the pickle module to load the cookies from a binary file and adds each cookie to the driver.

    Arguments:
        driver: selenium webdriver
        input_path: str, path to the file containing the cookies
    """
    with open(input_path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    logging.info(f"Cookies loaded from {input_path}") 

def clean_input_list(input_list) -> list:
    """
    Cleans the input list by removing duplicates and filtering out inactive companies.
    It reads the input file, checks for specific columns, and filters the data accordingly.

    Arguments:
        input_list: str, path to the input file containing company names
    Returns:
        list: a cleaned list of company names
    """
    df = pd.read_csv(input_list) 

    if 'Entrepreneur Stage' in df.columns:
        df = df[(df['Entrepreneur Stage'] != 'Inactive')]
    elif 'UEI' in df.columns:
        df = df[(df['UEI'] == '')]

    input_list = df["Company"].drop_duplicates().tolist()

    return input_list 

def main(input_file, starting_batch, output_path) -> None:
    """
    Main function to execute the SAM.gov scraper.
    It initializes the Selenium WebDriver, loads cookies, selects filters, and processes the input list in batches.
    It saves the scraped data to CSV files in the specified output path.

    Arguments:
        input_file: str, path to the input file containing company names
        starting_batch: int, batch number to start processing from
        output_path: str, path to save the output CSV files
    """

    starting_batch = int(starting_batch)
    
    input_list = clean_input_list(input_file)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://sam.gov/")
        
        load_cookies(driver, "sam/cookies.pkl")
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
    """
    Parses command line arguments using argparse.
    It defines the expected arguments and their types, and returns the parsed arguments.

    Arguments:
        arglist: list of command line arguments
    Returns:
        Namespace: parsed arguments
    """
    parser = ArgumentParser()
    parser.add_argument("--starting_batch", "-s", required=False, default = 0, help="Starting Batch")
    parser.add_argument("--input_file", "-i", required=True, help="Input File")
    parser.add_argument("--output_path", "-o", required=True, help = "Output Path")
    parser.add_argument("--log_file", "-l", required=False, default="log/sam_log.txt", help = "Log File")
   
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    logging.basicConfig(filename=f'{args.output_path}/{args.log_file}', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    main(args.input_file, args.starting_batch, args.output_path)
