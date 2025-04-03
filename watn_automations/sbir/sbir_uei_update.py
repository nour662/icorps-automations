from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from lxml import html
import pandas as pd
from datetime import datetime
from time import sleep
import os
import glob


# Function to fetch the search results and extract the link to the first result
def get_first_result_link(driver, uei, company_pages):
    driver.get("https://www.sbir.gov/portfolio")
    
    try: 
        # fill in uei field
        input_field = driver.find_element(By.ID, 'edit-uei')
        input_field.clear()
        input_field.send_keys(uei)
        
        #search using uei
        search_button = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.ID, 'edit-submit'))
        )
        #driver.execute_script("arguments[0].click()", search_button)
        #search_button.click()
        search_button.send_keys('\n')
        sleep(2)
    
        # Extract the first result link
        link_element = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, '//*[@id="search-results-hits"]/tbody/tr/td[1]/a'))
                                )
        link = link_element.get_attribute('href')
        # company_name = link_element.get_attribute('text')
     
        if link:
            company_pages[uei] = link
        else:
            print(f'{uei} search: None Found')
    except Exception as e:
        print(f"Failed to retrieve search results: {e}")
        
    return company_pages

# Function to fetch detailed page and extract information
def scrape_company_profile(profile_page_url):
    response = requests.get(profile_page_url)

    if response.status_code == 200:
        tree = html.fromstring(response.content)

        name_xpath = '//*[@id="block-sbir-content"]/section[2]/h2/text()'
        address_xpath = '//*[@id="block-sbir-content"]/section[2]/div/div[1]/div[1]/address/text()'
        website_xpath = '//*[@id="block-sbir-content"]/section[2]/div/div[1]/div[1]/p/a/@href'
        employee_xpath = '//*[@id="block-sbir-content"]/section[2]/div/div[1]/div[2]/p[2]/text()'
        
        company_name = tree.xpath(name_xpath)

        full_address = tree.xpath(address_xpath)        
        addr_list1 = full_address[0].split(",")
        if len(addr_list1) > 1:
            street_address = addr_list1[0]
        else: 
            street_address = full_address[0]  
        addr_list2 = full_address[1].split(",")
        city = addr_list2[0]
        state = addr_list2[1]
        zip_code = addr_list2[2]
            
        website = tree.xpath(website_xpath)
        employee_count = tree.xpath(employee_xpath)

        # Clean extracted data
        company_name = company_name[0].strip() if company_name else "N/A"
        print(company_name)
        street_address = street_address.strip().title() if street_address else "N/A"
        print(street_address)
        city = city.strip().title() if city else "N/A"
        print(city)
        state = state.strip() if state else "N/A"
        print(state)
        zip_code = zip_code.strip() if zip_code else "N/A"
        print(zip_code)
        website = website[0].strip() if website else "N/A"
        print(website)
        employee_count = employee_count[0].strip() if employee_count else "N/A"
        print(employee_count)

        # Create a DataFrame for this company's data
        company_df = pd.DataFrame([{
            "Name": company_name,
            "Street Address": street_address,
            "City": city,
            "State": state,
            "Zip Code": zip_code,
            "Website": website,
            "Employee Count": employee_count,
            "SBIR Profile Link": profile_page_url
        }])
        
        return company_df, company_name
    else:
        print(f"Failed to retrieve detailed page: {response.status_code}")
        return pd.DataFrame(), []

def download_awards(driver, company_name):
    driver.get("https://www.sbir.gov/awards")
    
    try: 
        # fill in company name field
        input_field = driver.find_element(By.ID, 'edit-company-name')
        input_field.clear()
        input_field.send_keys(company_name)
        
        #search using company name
        search_button = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.ID, 'edit-submit'))
        )
        search_button.send_keys('\n')
        sleep(2)
    
        try:
            '''this downloads the awards as a csv we can use this by extracting the csv
            direct all downloads from one folder to another'''
            # find the download button
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "downloadBtn"))
            )
            download_button.click()
        except Exception as e:
            print(f"Failed to download awards csv: {e}")  
    except Exception as e:
        print(f"Failed to find awards: {e}")
        
def delete_files_in_directory(directory_path):
   try:
     files = os.listdir(directory_path)
     for file in files:
       file_path = os.path.join(directory_path, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     print("All files deleted successfully.")
   except Exception as e:
     print("Error occurred while deleting files: {e}")
        
def merge_csv(directory):
    # Get the list of files in the directory and sort them by creation date
    all_award_files = glob.glob(f'{directory}/awards_search_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].csv')
    df_list = []
    for file in all_award_files:
        try:
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)
        except Exception as e:
            print(f"Error reading {file}: {e}")
    merged_df = pd.concat(df_list, ignore_index= True)
    return merged_df
    # merged_df.to_csv(f'sbir/full_award_search_uncleaned.csv', index=False)

def format_date(date_str):
    """Convert date from YYYY-MM-DD to MM/DD/YYYY format."""
    try:
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime('%m/%d/%Y')
    except ValueError:
        return date_str  # Return the original string if parsing fails

# Function to scrape funding records from award pages
def scrape_award_df(award_df):
    # Extract data using the column names of the given dataframe
    keyword_search = award_df['Company Name'].to_list()
    company_name = award_df['Company Name'].to_list()
    uei = award_df['UEI'].to_list()
    award_start_date = award_df['Proposal Award Date'].to_list()
    award_end_date = award_df['Contract End Date'].to_list()
    amount = award_df['Award Amount'].to_list()
    phase = award_df['Phase'].to_list()
    program = award_df['Program'].to_list()
    solicitation_number = award_df['Solicitation Number'].to_list()

    # Format award amount
    formatted_award_amount = []
    for num in amount: 
        formatted_award_amount.append(f"${num:,.2f}")
        
    # Format dates
    formatted_award_start_date = []
    for start_date in award_start_date:
        formatted_award_start_date.append(format_date(start_date))
        
    formatted_award_end_date = []
    for end_date in award_end_date:
        formatted_award_end_date.append(format_date(end_date))
        
    # Format Solicitation Number
    formatted_award_SN = []
    for snum in solicitation_number:
        if not isinstance(snum, str):
            formatted_award_SN.append("N/A")
        else:
            formatted_award_SN.append(snum)

    # Return the scraped data as a dictionary including the award URL
    funding_records= {
        "Keyword Search": keyword_search,
        "Company Name": company_name,
        'UEI': uei,
        "Start Date": formatted_award_start_date,
        "End Date": formatted_award_end_date,
        "Funding Amount": formatted_award_amount,
        "Phase": phase,
        "Program": program,
        "Solicitation Number": formatted_award_SN,
    }
    
    # Save funding records to a CSV file
    df_funding = pd.DataFrame.from_dict(funding_records)
    df_funding.to_csv('watn_automations\\sbir\\sbirsttr_funding.csv', index=False)
 
def main():   
    # Set up the driver and directory  
    chrome_options = Options()
    directory = "C:\\Users\\Pineappleboss.MGP\\Downloads\\sbir_award_downloads" # Set own download directory
    
    prefs = {
        "download.default_directory": directory,  
        "download.prompt_for_download": False,       # Disable download prompt
        "safebrowsing.enabled": True                 # Enable safe browsing
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--remote-debugging-port=9222')
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    
    df = pd.read_csv("watn_automations\\sbir\\UEI_test_list.csv")
    #uei_list = df.to_list()
    #uei_list = df[df["num_uei"]].to_list()
    uei_list = df['num_uei'].tolist()

    company_info_df = pd.DataFrame(columns=[
        "Name", "Street Address", "City", "State", "Zip Code", "Website", "Employee Count" , "SBIR Profile Link"
    ])
    company_pages = {}
    delete_files_in_directory(directory)

    # Iterate through the list of UEIs and fetch the corresponding page links
    for uei in uei_list:
        company_pages = get_first_result_link(driver, uei, company_pages)
        profile_page_url = company_pages.get(uei)
        print(profile_page_url)
        if profile_page_url:
            company_df, company_name = scrape_company_profile(profile_page_url)
            company_info_df = pd.concat([company_info_df, company_df], ignore_index=True)
            download_awards(driver, company_name)
    
    # merge award CSV files and get funding csv       
    full_award_df = merge_csv(directory)
    scrape_award_df(full_award_df)
    
    # Save company information to a CSV file
    company_info_df.to_csv('watn_automations\\sbir\\company_info_sbirsttr_db.csv', index=False)
    
if __name__ == "__main__":
    main()