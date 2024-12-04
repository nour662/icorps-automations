import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from random import randint
from urllib.parse import quote_plus

"""
This program is designed to search the SEC EDGAR Database to collect all of the filings for the companies who's names
are listed on the "input.csv" file. 

If a company is listed on the EDGAR Database, 2 things would occur:
1. All of the compnanies filings for the past 5 years would be downloaded to the computer
2. cik_data.csv: This .csv file will contain each successfully located companies name as well as their CIK Number

Please know that company name is not a unique search term, unlike a CIK. Because of this, the filings for multiple 
companies with the same name will be save and the same company name, and its CIK, will appear on the outputted .csv
file. 
"""

# Base URL for EDGAR search
#BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
base = "https://www.sec.gov/search-filing"

# Function to search for the CIK and filings for a given company name
def search_edgar(company_name):
    encoded_company_name = quote_plus(company_name)  
    params = {
        'action': 'getcompany',
        'company': encoded_company_name,
        'type': '',
        'dateb': '',
        'owner': 'exclude',
        'start': '',
        'output': 'atom',
        'count': '100'
    }
    response = requests.get(BASE_URL, params=params)
    
    #Checks to see if the webpage is active and prints out the company name if it cannot be found
    if response.status_code != 200:
        print(f"Failed to retrieve data for {company_name}")
        return None

    soup = BeautifulSoup(response.text, 'xml')
    entries = soup.find_all('entry')

    if not entries:
        print(f"No data found for {company_name}")
        return None

    #Extract CIK from each entry
    if entries[0].find('CIK'):
         cik= entries[0].find('CIK').text
    else:
        cik= 'N/A'
    filings = []

    #Collects all links and titles for the filings for each entry that reached an active webpage
    for entry in entries:
        title = entry.title.text if entry.title else 'N/A'
        link = entry.link['href'] if entry.link else 'N/A'
        filings.append({'title': title, 'link': link})

    return cik, filings

#Function to download each filing
def download_filing(filing_link, save_path, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(filing_link, timeout=10)
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {save_path}")
            return True
        
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(randint(1, 3))  # Random sleep between retries
            else:
                print(f"Failed to download after {retries} attempts: {filing_link}")
                return False

#Main function that reads input file, saves filings, and outputs "cik_data.csv"
def main(input_file):
    # Reads the input file
    df = pd.read_csv(input_file)

    #Create a directory of all the filings from the past five years that the program found on EDGAR
    output_dir = "edgar_filings"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    company_data = []

    #Downloads the filings
    for company_name in df['CompanyName']:
        try:
            result = search_edgar(company_name)
            if result:
                cik, filings = result
                company_data.append({'CompanyName': company_name, 'CIK': cik})

                # Save to file
                company_file_path = os.path.join(output_dir, f"{company_name.replace(' ', '_')}.txt")
                with open(company_file_path, 'w') as file:
                    file.write(f"Company Name: {company_name}\n")
                    file.write(f"CIK: {cik}\n")
                    file.write("\nFilings:\n")
                    for filing in filings:
                        file.write(f"{filing['title']} - {filing['link']}\n")

                # Download filings
                for filing in filings:
                    filing_link = filing['link']
                    if filing_link != 'N/A':  # Check if link is valid
                        file_name = filing['title'].replace('/', '_').replace(' ', '_') + '.txt'
                        file_path = os.path.join(output_dir, file_name)
                        download_filing(filing_link, file_path)

                # Introduce random sleep for rate limiting
                time.sleep(randint(1, 3))
            else:
                print(f"No filings found for {company_name}")
        except Exception as e:
            print(f"Error processing {company_name}: {e}")

    #Save company data to edgar_filing folder
    output_csv_path = 'cik_data.csv'
    company_df = pd.DataFrame(company_data)
    company_df.to_csv(output_csv_path, index=False)
    print(f"Company data saved to {output_csv_path}")

    #Prints summary of what data iss found within the terminal
    for company, data in company_data:
        print(f"\n{company}:")
        print(f"  CIK: {data['CIK']}")
        print(f"  Number of Filings: {len(data['Filings'])}")
        for filing in data['Filings']:
            print(f"    - {filing['title']} ({filing['link']})")

#Takes in company names from the input.csv file
if __name__ == "__main__":
    input_file = 'input.csv'  
    main(input_file)