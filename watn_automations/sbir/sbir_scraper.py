import requests
import pandas as pd
import os
import logging
import argparse
from math import ceil
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

AWARD_FIELDS = [
    "Company Name", "award_title", "agency", "branch", "phase", "program",
    "agency_tracking_number", "contract", "proposal_award_date", "contract_end_date",
    "solicitation_number", "solicitation_year", "topic_code", "award_year",
    "award_amount", "award_link"
]

COMPANY_FIELDS = ["duns", "number_employees"]

session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504, 429],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)



def get_company_info(uei) -> dict:
    """
    Fetch company information from the SBIR API using the UEI.

    Arguments:
        uei : str : Unique Entity Identifier (UEI) of the company.
    Returns:
        dict : Company information including UEI, name, address, website, and SBIR profile link.
    """
    url = f"https://api.www.sbir.gov/public/api/firm?keyword={uei}"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                company_info = data[0]
                structured = {
                    "UEI": company_info.get("uei", "N/A"),
                    "Name": company_info.get("company_name", "N/A"),
                    "Street Address": company_info.get("address1", "N/A"),
                    "City": company_info.get("city", "N/A"),
                    "State": company_info.get("state", "N/A"),
                    "Zip Code": company_info.get("zip", "N/A"),
                    "Website": company_info.get("company_url", "N/A"),
                    "SBIR Profile Link": company_info.get("sbir_url", "N/A")
                }
                return structured, company_info
        else:
            logging.error(f"Failed to retrieve company info for UEI {uei}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching company info for UEI {uei}: {e}")
    return None, None

def get_award_info(company_name) -> list:
    """
    Fetch award information from the SBIR API using the company name.

    Arguments:
        company_name : str : Name of the company.
    Returns:
        list : List of awards associated with the company.
    """
    url = f"https://api.www.sbir.gov/public/api/awards?firm={company_name}"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to retrieve award info for {company_name}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching award info for {company_name}: {e}")
    return []

def process_batch(uei_batch, batch_number, company_output_dir, awards_output_dir) -> None:
    """
    Process a batch of UEIs to fetch company and award information.

    Arguments:
        uei_batch : list : List of UEIs to process.
        batch_number : int : Current batch number.
        company_output_dir : str : Directory to save company information CSV.
        awards_output_dir : str : Directory to save award information CSV.
    """
    company_info_records = []
    award_core_records = []

    for uei in uei_batch:
        logging.info(f"Processing UEI: {uei}")
        company_structured, company_raw = get_company_info(uei)
        if not company_structured or not company_raw:
            logging.warning(f"No company data found for UEI: {uei}")
            continue

        company_name = company_structured["Name"]
        awards = get_award_info(company_name)
        
        if not awards:
            placeholder_award = {
                "Company Name": company_name,
                **{field: "N/A" for field in AWARD_FIELDS if field != "Company Name"}
            }
            award_core_records.append(placeholder_award)
        else: 
            for award in awards:
                award["Company Name"] = company_name
                core_record = {field: award.get(field, "") for field in AWARD_FIELDS}
                award_core_records.append(core_record)

                company_structured.update({field: award.get(field, company_raw.get(field, "")) for field in COMPANY_FIELDS})

        company_info_records.append(company_structured)
        time.sleep(0.5)  # Sleep between requests to avoid rate limiting

    # Save batch files
    if len(company_info_records) > 0:
        company_df = pd.DataFrame(company_info_records)
        company_batch_filename = os.path.join(company_output_dir, f"batch_{batch_number}.csv")
        company_df.to_csv(company_batch_filename, index=False)
        logging.info(f"Saved company data: {company_batch_filename}")

    if len(award_core_records) > 0:
        award_df = pd.DataFrame(award_core_records)
        award_batch_filename = os.path.join(awards_output_dir, f"batch_{batch_number}.csv")
        award_df.to_csv(award_batch_filename, index=False)
        logging.info(f"Saved award data: {award_batch_filename}")

def process_batches(uei_list, output_path, batch_size) -> None:
    """
    Process the list of UEIs in batches.

    Arguments:
        uei_list : list : List of UEIs to process.
        output_path : str : Directory to save output folders.
        batch_size : int : Number of UEIs to process per batch.
    """
    os.makedirs(output_path, exist_ok=True)

    company_dir = os.path.join(output_path, "sbir_batches/sbir_company_info_batches")
    awards_dir = os.path.join(output_path, "sbir_batches/sbir_awards_batches")
    os.makedirs(company_dir, exist_ok=True)
    os.makedirs(awards_dir, exist_ok=True)

    total_batches = ceil(len(uei_list) / batch_size)

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = start + batch_size
        uei_batch = uei_list[start:end]
        logging.info(f"Processing batch {batch_num + 1}/{total_batches} with {len(uei_batch)} UEIs")
        process_batch(uei_batch, batch_num + 1, company_dir, awards_dir)

def main(input_file, output_path, batch_size) -> None:
    """
    Main function to read input file and process batches.

    Arguments:
        input_file : str : Path to input CSV file with UEIs.
        output_path : str : Directory to store output folders.
        batch_size : int : Number of UEIs to process per batch.
    """
    log_dir = os.path.join(output_path, "log")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(filename=f'{output_path}/log/sbir_log.txt',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')    
    df = pd.read_csv(input_file)
    uei_list = df['UEI'].dropna().tolist()
    process_batches(uei_list, output_path, batch_size)

def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace : Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="SBIR API Scraper Script (Batch Mode)")
    parser.add_argument("--input_file", "-i", type=str, required=True, help="Path to input CSV file with UEIs.")
    parser.add_argument("--output_path", "-o", type=str, required=True, help="Directory to store output folders.")
    parser.add_argument("--batch_size", "-b", type=int, default=25, help="Number of UEIs to process per batch.")
    parser.add_argument("--starting_batch", "-s", type=int, default=0, help="Starting batch number to process.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    main(args.input_file, args.output_path, args.batch_size)