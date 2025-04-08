import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
print("Current working directory:", os.getcwd())
print("Files in current directory:", os.listdir())

def fetch_company_data(uei):
    """
    Fetches company data from SBIR.gov portfolio using the provided UEI.
    """
    base_url = "https://www.sbir.gov/portfolio"
    params = {'uei': uei}
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for UEI {uei}. HTTP Status Code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'lxml')

    # Extract Company Name
    company_name_tag = soup.find('h2', class_='company-title')
    company_name = company_name_tag.text.strip() if company_name_tag else 'N/A'

    # Extract Address
    address_tag = soup.find('div', class_='company-address')
    address = ' '.join(address_tag.stripped_strings) if address_tag else 'N/A'

    # Extract Number of Awards
    awards_tag = soup.find('div', class_='company-awards')
    number_of_awards = awards_tag.text.strip().split()[0] if awards_tag else '0'

    return {
        'UEI': uei,
        'Company Name': company_name,
        'Address': address,
        '# of Awards': number_of_awards
    }

def main(input_csv, output_csv):
    """
    Main function to read UEIs from input CSV, fetch company data, and write to output CSV.
    """
    import os
    print(f"Current working directory: {os.getcwd()}")
    print(f"Looking for file: {os.path.abspath(input_csv)}")
    # Read input CSV
    df = pd.read_csv(input_csv)

    # Ensure 'UEI' column exists
    if 'UEI' not in df.columns:
        print("Input CSV must contain a 'UEI' column.")
        return

    results = []

    for index, row in df.iterrows():
        uei = row['UEI']
        print(f"Processing UEI: {uei}")
        company_data = fetch_company_data(uei)
        if company_data:
            results.append(company_data)
        time.sleep(1)  # Respectful delay between requests

    # Create DataFrame from results
    results_df = pd.DataFrame(results)

    # Write to output CSV
    results_df.to_csv(output_csv, index=False)
    print(f"Data successfully written to {output_csv}")

if __name__ == "__main__":
    input_csv = 'input_file.csv'  # Replace with your input CSV file path
    output_csv = 'output_file.csv'  # Desired output CSV file path
    main(input_csv, output_csv)
import csv
import requests
import re   