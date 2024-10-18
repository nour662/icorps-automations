import requests
from lxml import html
import pandas as pd
from datetime import datetime
import time
import os
import random

# Function to fetch the search results and extract the link to the first result
def get_result_link(company_name, company_pages):
    search_url = f'https://legacy.www.sbir.gov/sbirsearch/firm/all?firm={company_name}&uei=&city=&zip=&page=1'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }
    response = requests.get(search_url, headers=headers)

    # Checks to see if the request to the server was successful
    if response.status_code == 200:
        tree = html.fromstring(response.content)

        # Extract the first result link
        links = tree.xpath('//table//tr/td[1]/a/@href')

        # Sorts through the results of the original database search
        if links:
            to_set_list = []
            for link in links:
                to_set = 'https://legacy.www.sbir.gov' + link
                to_set_list.append(to_set)

            company_pages[company_name] = to_set_list
        else:
            print(f"Failed to retrieve search results for company: {company_name}")

    return company_pages

# Function to fetch detailed page and extract information
def scrape_company_profile(profile_page_url , keyword):
    response = requests.get(profile_page_url)
    
    if response.status_code == 200:
        tree = html.fromstring(response.content)

        name_xpath = '//h1[@class="page-header"]/text()'
        street_address_xpath = '//span[@itemprop="streetAddress"]/text()'
        city_xpath = '//span[@itemprop="addressLocality"]/text()'
        state_xpath = '//span[@itemprop="addressRegion"]/text()'
        zip_xpath = '//span[@itemprop="postalCode"]/text()'
        website_xpath = '//a[@title="Company Website"]/@href'
        employee_xpath = '//div[@class="row open-style"]//div[@class="col-md-4"][2]//p[strong[contains(text(), "# of Employees:")]]/text()'
        uei_xpath = '//p[strong[text()="UEI:"]]/text()'

        company_name = tree.xpath(name_xpath)
        street_address = tree.xpath(street_address_xpath)
        city = tree.xpath(city_xpath)
        state = tree.xpath(state_xpath)
        zip_code = tree.xpath(zip_xpath)
        website = tree.xpath(website_xpath)
        employee_count = tree.xpath(employee_xpath)
        uei  = tree.xpath(uei_xpath)

        # Clean extracted data
        company_name = company_name[0].strip() if company_name else "N/A"
        street_address = street_address[0].strip().title() if street_address else "N/A"
        city = city[0].strip().title() if city else "N/A"
        state = state[0].strip() if state else "N/A"
        zip_code = zip_code[0].strip() if zip_code else "N/A"
        website = website[0].strip() if website else "N/A"
        employee_count = employee_count[0].strip() if employee_count else "N/A"
        uei = uei[0].strip() if uei else "N/A"

        # Create a DataFrame for this company's data
        company_df = pd.DataFrame([{
            "Keyword" : keyword, 
            "Name": company_name,
            "Street Address": street_address,
            "City": city,
            "State": state,
            "Zip Code": zip_code,
            "Website": website,
            "Employee Count": employee_count,
            "UEI" : uei, 
            "SBIR Profile Link": profile_page_url

        }])

        # Extract award links
        awards_xpath = '//div[@class="firm-details-content"]//h3/a/@href'
        awards_links = tree.xpath(awards_xpath)

        # Return the DataFrame and the list of award links
        return company_df, [f'https://legacy.www.sbir.gov{link}' for link in awards_links]
    else:
        print(f"Failed to retrieve detailed page for {profile_page_url}: {response.status_code}")
        return pd.DataFrame(), []

def format_date(date_str):
    """Convert date from YYYY-MM-DD to MM/DD/YYYY format."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d/%Y')
    except ValueError:
        return date_str  # Return the original string if parsing fails

# Function to scrape funding records from award pages
def scrape_award_page(award_url, company_name):
    response = requests.get(award_url)
    if response.status_code == 200:
        tree = html.fromstring(response.content)

        # Define the XPaths for various fields
        award_start_date_xpath = '//span[@class="open-label" and contains(text(), "Award Start Date (Proposal Award Date):")]/following-sibling::span[@class="open-description"]/text()'
        award_end_date_xpath = '//span[@class="open-label" and contains(text(), "Award End Date (Contract End Date):")]/following-sibling::span[@class="open-description"]/text()'
        duns_num_xpath = '//div[@class="row open-style"]//span[@class="open-label" and contains(text(), "DUNS:")]/following-sibling::span[@class="open-description"]/text()'
        amount_xpath = '//div[@class="row open-style"]//span[@class="open-label" and contains(text(), "Amount:")]/following-sibling::span[@class="open-description"]/text()'
        phase_xpath = '//div[@class="row open-style"]//span[@class="open-label" and contains(text(), "Phase:")]/following-sibling::span[@class="open-description"]/text()'
        program_xpath = '//div[@class="row open-style"]//span[@class="open-label" and contains(text(), "Program:")]/following-sibling::span[@class="open-description"]/text()'
        solicitation_number_xpath = '//div[@class="row open-style"]//span[@class="open-label" and contains(text(), "Solicitation Number:")]/following-sibling::span[@class="open-description"]/text()'
        company_name_xpath = '//div[@class="sbc-name-wrapper"]/a/text()'

        # Extract data using the defined XPaths
        award_start_date = tree.xpath(award_start_date_xpath)
        award_end_date = tree.xpath(award_end_date_xpath)
        duns_num = tree.xpath(duns_num_xpath)
        amount = tree.xpath(amount_xpath)
        phase = tree.xpath(phase_xpath)
        program = tree.xpath(program_xpath)
        solicitation_number = tree.xpath(solicitation_number_xpath)
        company_name = tree.xpath(company_name_xpath)

        # Format dates
        formatted_award_start_date = format_date(award_start_date[0].strip()) if award_start_date else "N/A"
        formatted_award_end_date = format_date(award_end_date[0].strip()) if award_end_date else "N/A"

        # Return the scraped data as a dictionary including the award URL
        return {
            "Keyword Search": company_name[0].strip() if company_name else "N/A",
            "Company Name": company_name[0].strip() if company_name else "N/A",
            "Start Date": formatted_award_start_date,
            "End Date": formatted_award_end_date,
            "Funding Amount": amount[0].strip() if amount else "N/A",
            "Phase": phase[0].strip() if phase else "N/A",
            "Program": program[0].strip() if program else "N/A",
            "Solicitation Number": solicitation_number[0].strip() if solicitation_number else "N/A",
            "Source Link": award_url
        }
    else:
        print(f"Failed to retrieve award page: {response.status_code}")
        return None

    


def main(input_file='input.csv', start_batch=107, batch_size=10):
    # Load the companies from input.csv
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found.")
        return
    
    # Read company names from the CSV (assuming company names are in a column called 'Company Name')
    companies_df = pd.read_csv(input_file)
    if 'Company_Name' not in companies_df.columns:
        print("The CSV must contain a 'Company_Name' column.")
        return
    
    companies = companies_df['Company_Name'].tolist()

    # Create directories if they don't exist
    if not os.path.exists('company_output'):
        os.makedirs('company_output')
    if not os.path.exists('award_output'):
        os.makedirs('award_output')

    company_pages = {}
    total_batches = (len(companies) + batch_size - 1) // batch_size  # Total number of batches

    for batch_num in range(start_batch, total_batches + 1):
        print(f"Processing batch {batch_num}/{total_batches}")
        print()
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, len(companies))
        batch_companies = companies[start_idx:end_idx]

        all_company_info = pd.DataFrame()  # DataFrame to store all company data in the batch
        all_award_info = pd.DataFrame()    # DataFrame to store all award data in the batch

        # Process each company in the batch
        for company_name in batch_companies:
            print(f"Processing company: {company_name}")
            company_pages = get_result_link(company_name, company_pages)

            if company_name in company_pages:
                for profile_page_url in company_pages[company_name]:
                    # Scrape company profile and award links
                    company_df, award_links = scrape_company_profile(profile_page_url,company_name)

                    # Append company info to the batch DataFrame
                    all_company_info = pd.concat([all_company_info, company_df], ignore_index=True)

                    # Scrape and append award info
                    for award_url in award_links:
                        award_info = scrape_award_page(award_url, company_name)
                        if award_info:
                            all_award_info = pd.concat([all_award_info, pd.DataFrame([award_info])], ignore_index=True)

        # Save the company and award info to CSV files in their respective directories
        company_csv_path = f'company_output/company_batch_{batch_num}.csv'
        award_csv_path = f'award_output/award_batch_{batch_num}.csv'
        
        if not all_company_info.empty:
            all_company_info.to_csv(company_csv_path, index=False)
            print(f"Saved company information for batch {batch_num} to {company_csv_path}")
        else:
            print(f"No company information to save for batch {batch_num}")

        if not all_award_info.empty:
            all_award_info.to_csv(award_csv_path, index=False)
            print(f"Saved award information for batch {batch_num} to {award_csv_path}")
        else:
            print(f"No award information to save for batch {batch_num}")

        time.sleep(5)  


if __name__  == "__main__": 
    main()