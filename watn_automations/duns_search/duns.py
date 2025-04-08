import argparse
import pandas as pd
import requests
import re

import pandas as pd
import requests
import re

def get_firm_info_by_duns(duns_number):
    """Fetch firm details using DUNS number from the SBIR API."""
    BASE_URL = "https://api.www.sbir.gov/public/api/firm"
    
    params = {'duns': duns_number}
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        firm_data = response.json()
        return firm_data[0] if firm_data else None
    return None

def process_salesforce_companies(input_file, output_file):
    """Process Salesforce companies and search for their SBIR data using only DUNS number."""
    # Step 1: Read the input CSV file containing Salesforce company names and DUNS numbers
    df = pd.read_csv(input_file,  dtype={'DUNS Number': str})
    
    # Step 2: Initialize columns for firm name and UEI
    df['Firm Name'] = None
    df['UEI'] = None
    
    # Step 3: Loop through each company in the DataFrame
    for index, row in df.iterrows():
        firm_name = row.get('Account Name')  
        duns_number = row.get('DUNS Number')  
        
        print(f"Processing {firm_name} with DUNS: {duns_number}")
        
        # Step 4: Search the SBIR API using DUNS number
        firm_info = get_firm_info_by_duns(duns_number)
        
        if firm_info:
            # Extract firm name and UEI
            df.at[index, 'Firm Name'] = firm_info.get('company_name', None)
            df.at[index, 'UEI'] = firm_info.get('uei', None)
        else:
            print(f"No data found for DUNS: {duns_number}")
    
    # Step 5: Save the results to a new CSV
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    input_file = 'duns_no_uei.csv'
    output_file = 'updated_duns.csv'

    process_salesforce_companies(input_file, output_file)
