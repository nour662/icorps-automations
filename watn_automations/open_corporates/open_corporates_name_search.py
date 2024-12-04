import pandas as pd
from time import sleep
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
This script searches the Open Corporates government database for companies of interest using the company entrepeneurs name's in 
the "input.csv" file. The script will universalize the individuals name's by removing any title such as excess spaces or incorrect
capitalization, in order to make it a better seach term and optimize the results outputed. The program will run the input file's 
records at 10  records each time to minimize loss in the result of a crash. The format of the output will be as follows: 

keyword, individuals_name, company_name, position, other_officers

The results will appear as .csv files named "batch_1.csv", "batch_2.csv", ect. As entrepeneur's names are not a unique search term,
multiple records could appear as the result of a singular search, and therfore the output will need to be cleaned. In order to 
ease the cleaning process, it is recommend to merge all batches into one large file. 

It is important to note that only the first 25 records that appear after the name is searched will be recoreded in the ouput .csv 
batches. If a name is not found on the Open Corporates Database, the name will be outputted in the terminal sahying no results 
could be found.

**Nour Ali Ahmed**
**Scott Lucarelli**
"""

# Creates a function that enters in the keyword term and searchs it through the "Open Corporates" Database
def search_keyword(driver, keyword):
    try:
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@class="oc-header-search__input js-oc-search-input"]'))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="oc-header-search__button"]'))
        )

        search_bar.send_keys(keyword)
        submit_button.click()

        sleep(5)
        
        # Returns the links of the first 25 results for each keyword search for data scraping later
        links = driver.find_elements(By.XPATH, '//a[@class="officer inactive"]')
        return [a.get_attribute('href') for a in links][:25]
    
    # Prints in terminal if the name recieved no results in the database
    except Exception as e:
        print(f"Error searching keyword {keyword}: {e}")
        return []

# Scrapes the indidual peoples pages fort he Company Name, Individual's Name, Position, and Other Officers Name's 
def scrape_links(driver, keyword, url):
    try:
        driver.get(url)
        sleep(5)

        def safe_find(xpath):
            try:
                return driver.find_element(By.XPATH, xpath).text
            except Exception:
                return None
        
        company_name = safe_find('//a[@class="company branch active"]')
        name = safe_find('//dd[@class="name"]')
        position = safe_find('//dd[@class="position"]')
        other_officers = safe_find('//ul[@class="officers"]')
        """
        officer_dict = {}
        i = 1 
        while i <= len(other_officers):
            officer_dict[i] = other_officers[i+1]
            i+=2
        """
        return {
            "keyword": keyword,
            "individuals_name": name,
            "company_name": company_name,
            "position": position, 
            "other_officers": other_officers,
        }
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Universalizes each search term through removing excess spaces or incorrect capitalization 
def process_batch(driver, input_list, start, end):
    
    batch_input = input_list[start:end]

    names_list = {}
    for name in batch_input:
        name = str(name)
        search_input = name.lower().strip()
        result_links = search_keyword(driver, search_input)
        names_list[name] = result_links

# Collects each indiviual webpage for all records
    links_data = []
    for keyword, urls in names_list.items():
        for url in urls:
            result = scrape_links(driver, keyword, url)
            if result:
                links_data.append(result)

    return links_data

# Reads the input file, lauches Chrome to begin search process, and returns .csv result files in batches 
def main(starting_batch=0):
    input_df = pd.read_csv(r":C:\Users\sluca\Downloads\icorps-data\watn_automations\open_corporates\name_input.csv") #Calls to an external .csv file which contains the company names (User input)
    input_list = input_df["People_Name"].tolist()

    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://opencorporates.com/officers")
        sleep(60)
        
        batch_size = 10 
        num_batches = math.ceil(len(input_list) / batch_size)

        if not os.path.exists("output"):
            os.makedirs("output")

        # Seperates the input file in batches to run through the script. Limits data loss if the program crashes
        for i in range(starting_batch, num_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(input_list))
            print(f"Processing batch {i+1}/{num_batches}, companies {start_idx+1} to {end_idx}")

            batch_data = process_batch(driver, input_list, start_idx, end_idx)

            output_df = pd.DataFrame(batch_data)

            output_filename = f"output/batch_{i+1}.csv"
            output_df.to_csv(output_filename, index=False)
            print(f"Batch {i+1} completed and saved to {output_filename}")
            driver.get("https://opencorporates.com/officers")
    
    finally:
        driver.quit()

# If the program does crash, allows for user to pick up batch processing where it ended to eliminate duplicate output files
if __name__ == "__main__":
    starting_batch = int(input("Enter the batch number to start from: "))
    main(starting_batch)
