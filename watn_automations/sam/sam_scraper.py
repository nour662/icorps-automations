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

def search_keyword(driver, keyword) -> list:
    """Search for a keyword on the SAM website and return the first 10 links found.

    Arguments:
        driver (webdriver): The Selenium WebDriver instance.
        keyword (str): The keyword to search for.
    Returns:
        list: A list of URLs found in the search results.
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
        except:
            pass  

        links = WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.XPATH, '//div[@class="grid-row grid-gap"]//a')
        )

        return [a.get_attribute('href') for a in links][:10]

    except Exception as e:
        logging.error(f"Error searching keyword {keyword}: {e}")
        return []

def scrape_links(driver, keyword, url) -> dict:
    """Scrape data from a given URL on the SAM website.

    Arguments:
        driver (webdriver): The Selenium WebDriver instance.
        keyword (str): The keyword used for the search.
        url (str): The URL to scrape data from.
    Returns:
        dict: A dictionary containing the scraped data.
    """
    try:
        logging.info(f"Scraping URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@class="sds-navbar__title"]')))

        def safe_find(xpath):
            try:
                return driver.find_element(By.XPATH, xpath).text
            except:
                return None

        def safe_find_attr(xpath, attr):
            try:
                return driver.find_element(By.XPATH, xpath).get_attribute(attr)
            except:
                return None

        def safe_find_contacts(xpath, attr):
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                return [element.get_attribute(attr) for element in elements]
            except:
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
                        full_name = f"{match.group(1).title()} {match.group(3).title()}"
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

        logging.info(f"Scraped data for {keyword}: {legal_name}, {num_uei}, {cage}, {result1}, {result2}, {entity_url}")

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
    """Process a batch of company names, search for them, and scrape data from the results.

    Arguments:
        driver (webdriver): The Selenium WebDriver instance.
        input_list (list): The list of company names to process.
        start (int): The starting index for the batch.
        end (int): The ending index for the batch.

    Returns:
        list: A list of dictionaries containing the scraped data for each company.
    """
    links = {}
    batch_input = input_list[start:end]

    for name in batch_input:
        name = str(name)
        search_input = re.sub(r"\b(inc|llc|corp|ltd|limited|pty)\b", "", name.lower().strip())
        search_input = search_input.replace(".", "").replace(",", "")
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
    """Select filters on the SAM website to narrow down search results.

    Arguments:
        driver (webdriver): The Selenium WebDriver instance.
    """
    try:
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@id = "search"]'))
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

def load_cookies(driver, input_path) -> None:
    """Load cookies from a file and add them to the Selenium WebDriver.

    Arguments:
        driver (webdriver): The Selenium WebDriver instance.
        input_path (str): The path to the file containing the cookies.
    """
    with open(input_path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    logging.info(f"Cookies loaded from {input_path}")

def clean_input_list(input_file) -> list:
    """Clean the input list by removing duplicates and filtering based on conditions.

    Arguments:
        input_file (str): The path to the input CSV file.
    Returns:
        list: A cleaned list of company names.
    """
    df = pd.read_csv(input_file) 
    if 'Entrepreneur Stage' in df.columns:
        df = df[(df['Entrepreneur Stage'] != 'Inactive')]
    elif 'UEI' in df.columns:
        df = df[(df['UEI'] == '')]
    return df["Company"].drop_duplicates().tolist()

def main(input_file, starting_batch, output_path, headless=False) -> None:
    """Main function to initialize the WebDriver, process batches of company names, and save results.

    Arguments:
        input_file (str): The path to the input CSV file.
        starting_batch (int): The starting batch number for processing.
        output_path (str): The path to save the output files.
        headless (bool): Whether to run the browser in headless mode.
    """
    starting_batch = int(starting_batch)
    input_list = clean_input_list(input_file)

    chrome_options = Options()
    if str(headless).lower() == "true":
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
            
            driver.get("https://sam.gov/")
            select_filters(driver)

    finally:
        driver.quit()
        logging.info("Driver quit and process finished.")

def parse_args(arglist):
    """Parse command line arguments.

    Arguments:
        arglist (list): List of command line arguments.
    Returns:
        Namespace: Parsed arguments.
    """
    parser = ArgumentParser()
    parser.add_argument("--starting_batch", "-s", required=False, default=0, help="Starting Batch")
    parser.add_argument("--input_file", "-i", required=True, help="Input File")
    parser.add_argument("--output_path", "-o", required=True, help="Output Path")
    parser.add_argument("--headless", "-hd", required=False, default=True, help="Headless Mode")
    parser.add_argument("--log_file", "-l", required=False, default="log/sam_log.txt", help="Log File")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    logging.basicConfig(filename=f'{args.output_path}/{args.log_file}', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    main(args.input_file, args.starting_batch, args.output_path, headless=args.headless)
    logging.info("Script started.")