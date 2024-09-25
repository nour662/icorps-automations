
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import pandas as pd
import time

#df = pd.read_csv('name_list.csv')  # INPUT CSV!!! Please change this to the proper file you want to search through.
#data_list =df.values.tolist()
#print(data_list)





def search_name_and_scrape_info(driver, company_name, csv_filename):
    # Step 1: Modify the search URL with the desired keyword
    search_url = f"https://sam.gov/search/?page=1&pageSize=25&sort=-relevance&index=ei&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bkey%5D=%22{company_name}%22&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bvalue%5D=%22{company_name}%22&sfm%5Bstatus%5D%5Bis_active%5D=true&sfm%5Bstatus%5D%5Bis_inactive%5D=false"
    #search_url = f"https://sam.gov/search/?page=1&pageSize=25&sort=-modifiedDate&sfm%5BsimpleSearch%5D%5BkeywordRadio%5D=ALL&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bkey%5D=%22{company_name}%22&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bvalue%5D=%22{company_name}%22&sfm%5BsimpleSearch%5D%5BkeywordEditorTextarea%5D=&sfm%5Bstatus%5D%5Bis_active%5D=true"
    driver.get(search_url)
    time.sleep(4)
    print(company_name)
    # Step 2: Gather links from the search results
    try:
        # Locate the links using XPath that contains '/entity/' in their href
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/entity/")]'))
        )
        links = [result.get_attribute('href') for result in search_results]

    except TimeoutException:
        print("No results found for the given company name.")
        return

    # Initialize a list to store the records
    records = []

    # Step 3: Scrape details from each link
    for link in links:
        driver.get(link)
        time.sleep(2)  # Wait for the page to load
        
        try:
            # Use XPath to find each required field
            entity_name = driver.find_element(By.XPATH, '//h1').text  # Adjust XPath as needed

            # Scraping individual fields using XPath
            uei_sam = driver.find_element(By.XPATH, '//span[@id="ueiSAM"]').text
            legal_business_name = driver.find_element(By.XPATH, '//span[@id="legalBusinessName"]').text
            dba_name = driver.find_element(By.XPATH, '//span[@id="dbaName"]').text
            cage_code = driver.find_element(By.XPATH, '//span[@id="cageCode"]').text
            registration_status = driver.find_element(By.XPATH, '//span[@id="registrationStatus"]').text
            entity_url = driver.find_element(By.XPATH, '//a[@id="entityURL"]').get_attribute('href')
            
            # Construct address strings using XPath
            physical_address = driver.find_element(By.XPATH, '//div[@id="physicalAddress"]').text.replace('\n', ', ')
            mailing_address = driver.find_element(By.XPATH, '//div[@id="mailingAddress"]').text.replace('\n', ', ')

            primary_naics = driver.find_element(By.XPATH, '//span[@id="primaryNaics"]').text

            # Points of Contact (POC)
            poc_first_name = driver.find_element(By.XPATH, '//span[@id="pocFirstName"]').text
            poc_last_name = driver.find_element(By.XPATH, '//span[@id="pocLastName"]').text
            poc_title = driver.find_element(By.XPATH, '//span[@id="pocTitle"]').text
            duns = driver.find_element(By.XPATH, '//span[@id="duns"]').text  # Adjust as needed if D-U-N-S number exists

            # Construct the record with all scraped information
            record = {
                'SearchKeyword': company_name,
                'UEI': uei_sam,
                'LegalBusinessName': legal_business_name,
                'DBAName': dba_name,
                'CAGECode': cage_code,
                'RegistrationStatus': registration_status,
                'EntityURL': entity_url,
                'PhysicalAddress': physical_address,
                'MailingAddress': mailing_address,
                'PrimaryNAICS': primary_naics,
                'POCName': f"{poc_first_name} {poc_last_name}",
                'POCTitle': poc_title,
                'DUNS': duns
            }

            # Append the record to the list
            records.append(record)
            
        except NoSuchElementException as e:
            print(f"Failed to scrape data from {link}: {e}")

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--remote-debugging-port=9222')  # Use the same port as used to start Chrome

driver = webdriver.Chrome(options=chrome_options)

# Navigate to the search page
driver.get('')

# Read the CSV file containing names
df = pd.read_csv('name_list.csv')  # INPUT CSV!!! Please change this to the proper file you want to search through.
#data_list =df.values.tolist()
time.sleep(60)  # Adjusted the sleep time to avoid too long a wait.

# Iterate over each row in the DataFrame
first_name = driver.find_element(By.XPATH, '//span[@id="pocFirstName"]').text
last_name = driver.find_element(By.XPATH, '//span[@id="pocLastName"]').text
for index, row in df.iterrows():
    keywords = ['llc' , 'inc' , 'corp']
    company_name = row['last_name']  # INPUT ROW!!! Please change this to the name of the column containing the last name of the person.
    search_name_and_scrape_info(driver, first_name, last_name, df, index)

# Close the WebDriver
driver.quit()
print(df)

# Save the updated DataFrame to a CSV file
df.to_csv('engineering_DeansList_scraped.csv', index=False)



