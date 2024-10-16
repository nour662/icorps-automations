import requests
from lxml import html
import pandas as pd
from datetime import datetime
import time

# Function to fetch the search results and extract the link to the first result
def get_result_link(company_name, company_pages):
    search_url = f'https://legacy.www.sbir.gov/sbirsearch/firm/all?firm={company_name}&uei=&city=&zip=&page=1'
    response = requests.get(search_url)

    #Checks to see if the request to the server was successful
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
            print(f"Failed to retrieve search results: {company_name}")

    return company_pages


# Function to fetch detailed page and extract information
def scrape_company_profile(profile_page_url):
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

        company_name = tree.xpath(name_xpath)
        street_address = tree.xpath(street_address_xpath)
        city = tree.xpath(city_xpath)
        state = tree.xpath(state_xpath)
        zip_code = tree.xpath(zip_xpath)
        website = tree.xpath(website_xpath)
        employee_count = tree.xpath(employee_xpath)

        # Clean extracted data
        company_name = company_name[0].strip() if company_name else "N/A"
        street_address = street_address[0].strip().title() if street_address else "N/A"
        city = city[0].strip().title() if city else "N/A"
        state = state[0].strip() if state else "N/A"
        zip_code = zip_code[0].strip() if zip_code else "N/A"
        website = website[0].strip() if website else "N/A"
        employee_count = employee_count[0].strip() if employee_count else "N/A"

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

        # Extract award links
        awards_xpath = '//div[@class="firm-details-content"]//h3/a/@href'
        awards_links = tree.xpath(awards_xpath)

        # Return the DataFrame and the list of award links
        return company_df, [f'https://legacy.www.sbir.gov{link}' for link in awards_links]
    else:
        print(f"Failed to retrieve detailed page: {response.status_code}")
        return pd.DataFrame(), []

def format_date(date_str):
    """Convert date from YYYY-MM-DD to MM/DD/YYYY format."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d/%Y')
    except ValueError:
        return date_str  # Return the original string if parsing fails

# Function to scrape funding records from award pages
def scrape_award_page(award_url, names):
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
            "Keyword Search": names,
            "Company Name": company_name[0].strip() if company_name else "N/A",
            "Start Date": formatted_award_start_date,
            "End Date": formatted_award_end_date,
            "Funding Amount": amount[0].strip() if amount else "N/A",
            "Phase": phase[0].strip() if phase else "N/A",
            "Program": program[0].strip() if program else "N/A",
            "Solicitation Number": solicitation_number[0].strip() if solicitation_number else "N/A",
            "Source Link" : award_url
        }
    else:
        print(f"Failed to retrieve award page: {response.status_code}")
        return None
    


def main(): 
    df = pd.read_csv('../sam_gov/input.csv')
    company_list = df['Company_Name'].tolist()

    #To universalize the company names and remove inconsistencies
    lowercase_list = list(map(str.lower,company_list))
    cleaned_list = [item.replace(" inc", "") for item in lowercase_list]
    cleaned_list = [item.replace(" llc", "") for item in cleaned_list]
    cleaned_list = [item.replace(" corp", "") for item in cleaned_list]
    cleaned_list = [item.replace(" ltd", "") for item in cleaned_list]
    cleaned_list = [item.replace(" pty", "") for item in cleaned_list]
    cleaned_list = [item.replace(" limited", "") for item in cleaned_list]
    cleaned_list = [item.replace(",", "") for item in cleaned_list]
    cleaned_list = [item.replace(".", "") for item in cleaned_list]

    #To create the display of the "company_info_sbirsttr" page
    company_info_df = pd.DataFrame(columns=[
        "Keyword Search","Name", "Street Address", "City", "State", "Zip Code", "Website", "Employee Count" , "SBIR Profile Link"
    ])

    company_pages = {}
    funding_records = []


    # Iterate through the list of Company Name's and fetch the corresponding page links
    for company_name in cleaned_list:
        company_pages = get_result_link(company_name, company_pages)

    valid_names = []

    for names in company_pages.keys():
        profile_page_urls = company_pages[names]
        for page_url in profile_page_urls:
            profile_page_url = page_url
            if profile_page_url:
                valid_names.append(names)
                company_df, award_links = scrape_company_profile(profile_page_url)
                company_info_df = pd.concat([company_info_df, company_df], ignore_index=True)
                for award_link in award_links:
                    record = scrape_award_page(award_link, names)
                    if record:
                        funding_records.append(record)

    #Takes the search phrase and places it in the displayed record
    company_info_df = company_info_df.assign(**{"Keyword Search": valid_names})

    # Save company information to a CSV file
    company_info_df.to_csv('company_info_sbirsttr_db.csv', index=False)

    # Save funding records to a CSV file
    df_funding = pd.DataFrame(funding_records)
    df_funding.to_csv('sbirsttr_funding.csv', index=False)


if __name__  == "__main__": 
    main()