"""This script will search the UMD student directory for emails and other key pieces of information on a list of students. 
    For this scrtipt, you need the first name and the last name of the student. Once run, it will output a csv file including the following: 
        - Email 
        - School Status
        - Address
        - Phone Number
        - Job Title 
        - Department
        - School

For this script to run, you need to run the following commands in the terminal, in order: 

python -m venv myenv
source myenv/bin/activate
pip install selenium

The command run the script is : 

python3 search_umd_directory.py

If you are having any trouble, you can email me at nour1786@umd.edu or nourali1786@gmail.com 

Happly collecting, 
Nour

"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import pandas as pd
import time

def search_name_and_scrape_info(driver, first_name, last_name, df, index):
    try:
        # Expand the search form by clicking the dropdown
        drop_down_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'i.glyphicon.pull-right.glyphicon-chevron-down'))
        )
        drop_down_button.click()

        # Wait for the advanced search inputs to be visible
        first_name_search = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.ID, 'advancedSearchInputs.firstName'))
        )
        last_name_search = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.ID, 'advancedSearchInputs.lastName'))
        )

        # Clear and enter the name into the search input fields
        first_name_search.clear()
        last_name_search.clear()
        first_name_search.send_keys(first_name)
        last_name_search.send_keys(last_name)
        
        # Click the search button
        search_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"][name="advancedSearch"]'))
        )
        search_button.click()


        # Initialize lists to store the scraped data
        email_addresses, institutions, titles, depts, schools, addresses, phones = [], [], [], [], [], [], []

        # Scrape the data from the search results
        try:
            email_elements = driver.find_elements(By.XPATH, '//div[@class="email"]/a')
            email_addresses = [email_element.text for email_element in email_elements]
        except NoSuchElementException:
            email_addresses.append('No email found')

        try:
            institution_elements = driver.find_elements(By.XPATH, '//div[@class="institution"]')
            institutions = [institution_element.text for institution_element in institution_elements]
        except NoSuchElementException:
            institutions.append('No institution found')

        try:
            title_elements = driver.find_elements(By.XPATH, '//div[@class="displayTitle"]')
            titles = [title_element.text for title_element in title_elements]
        except NoSuchElementException:
            titles.append('No title found')

        try:
            dept_elements = driver.find_elements(By.XPATH, '//div[@class="deptName"]')
            for dept_element in dept_elements:
                parts = dept_element.text.split("-")
                school, dept = parts[0].strip(), '-'.join(parts[1:]).strip()
                schools.append(school)
                depts.append(dept)

        except NoSuchElementException:
            depts.append('No department found')

        try:
            address_elements = driver.find_elements(By.XPATH, '//div[@class="address"]')
            addresses = [address_element.text for address_element in address_elements]
        except NoSuchElementException:
            addresses.append('No address found')

        try:
            phone_elements = driver.find_elements(By.XPATH, '//div[@class="phoneNumbers"]')
            phones = [phone_element.text.split('Phone:')[-1].strip() for phone_element in phone_elements]
        except NoSuchElementException:
            phones.append('No phone found')

        # If no email addresses found, add 'person not found'
        if not email_addresses:
            email_addresses.append('person not found')

        print(f'{first_name} {last_name} found!')

        # Update the DataFrame with the information
        df.at[index, 'Email'] = '; '.join(email_addresses)
        df.at[index, 'Institution'] = '; '.join(institutions)
        df.at[index, 'Title'] = '; '.join(titles)
        df.at[index, 'Dept'] = '; '.join(depts)
        df.at[index, 'School'] = '; '.join(schools)
        df.at[index, 'Address'] = '; '.join(addresses)
        df.at[index, 'Phone'] = '; '.join(phones)

        print(df)

    except (ElementNotInteractableException, TimeoutException) as e:
        pass

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--remote-debugging-port=9222')  # Use the same port as used to start Chrome

driver = webdriver.Chrome(options=chrome_options)

# Navigate to the search page
driver.get('https://identity.umd.edu/search')

# Read the CSV file containing names
df = pd.read_csv('data/engeineering_DeansList.csv')  # INPUT CSV!!! Please change this to the proper file you want to search through.
time.sleep(30)  # Adjusted the sleep time to avoid too long a wait.

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    first_name = row['first_name']  # INPUT ROW!!! Please change this to the name of the column containing the first name of the person.
    last_name = row['last_name']  # INPUT ROW!!! Please change this to the name of the column containing the last name of the person.
    search_name_and_scrape_info(driver, first_name, last_name, df, index)

# Close the WebDriver
driver.quit()

# Save the updated DataFrame to a CSV file
df.to_csv('engineering_DeansList_scraped.csv', index=False)






