from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv
import os

# --- SETUP SELENIUM WEBDRIVER ---
# Configure Chrome to run headless (no GUI)
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Adjust the path to your local chromedriver if necessary
service = Service()  # Assumes chromedriver is in PATH
browser = webdriver.Chrome(service=service, options=options)

# --- SETUP INPUT/OUTPUT ---
input_file = "/Users/carterkinch/Documents/GitHub/icorps-automations/watn_automations/sbir/UEI_test_list.csv"
output_file = "/Users/carterkinch/Documents/GitHub/icorps-automations/watn_automations/sbir/scraped_sbir_output.csv"

# Confirm working directory and files
print("Input File Path:", input_file)
print("Output File Path:", output_file)

# --- READ UEIs FROM CSV ---
uei_list = []
with open(input_file, mode='r', newline='') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        uei = row.get('UEI')
        if uei:
            uei_list.append(uei.strip())

# --- SCRAPE DATA FOR EACH UEI ---
data_rows = []

for uei in uei_list:
    print(f"Processing UEI: {uei}")
    url = f"https://www.sbir.gov/portfolio?uei={uei}"
    browser.get(url)
    time.sleep(2)  # Wait for page to load (adjust delay if needed)

    try:
        # Extract Company Name using XPath
        company_name_elem = browser.find_element(By.XPATH, '//h2[contains(@class, "company-title")]')
        company_name = company_name_elem.text.strip()
    except:
        company_name = "N/A"

    try:
        # Extract Address block using XPath
        address_elem = browser.find_element(By.XPATH, '//div[contains(@class, "company-address")]')
        address = address_elem.text.strip().replace('\n', ' ')
    except:
        address = "N/A"

    try:
        # Extract Number of Awards using XPath (typically found near award results)
        awards_text_elem = browser.find_element(By.XPATH, '//div[@class="view-header"]')
        awards_text = awards_text_elem.text.strip()
        number_of_awards = ''.join([s for s in awards_text if s.isdigit()])
    except:
        number_of_awards = "0"

    # Save data row
    data_rows.append({
        'UEI': uei,
        'Company Name': company_name,
        'Address': address,
        '# of Awards': number_of_awards
    })

    time.sleep(1)  # Be respectful to the server

# --- WRITE OUTPUT TO CSV ---
with open(output_file, mode='w', newline='') as outfile:
    fieldnames = ['UEI', 'Company Name', 'Address', '# of Awards']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data_rows)

print(f"Finished. Data written to {output_file}")

# --- CLEANUP ---
browser.quit()
# Optionally, remove the input file if no longer needed