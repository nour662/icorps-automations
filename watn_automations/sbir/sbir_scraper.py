import requests
import pandas as pd
import os
import logging
import argparse
from math import ceil


def get_company_info(uei) -> dict:
    """
    Fetch company information from the SBIR API using the UEI.

    Arugments:
        uei : str : Unique Entity Identifier (UEI) of the company.
    Returns:
        ict : Company information including UEI, name, address, website, and SBIR profile link.
    """
    url = f"https://api.www.sbir.gov/public/api/firm?keyword={uei}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data:
            company_info = data[0] 
            return {
                "UEI": company_info.get("uei", "N/A"),
                "Name": company_info.get("company_name", "N/A"),
                "Street Address": company_info.get("address1", "N/A"),
                "City": company_info.get("city", "N/A"),
                "State": company_info.get("state", "N/A"),
                "Zip Code": company_info.get("zip", "N/A"),
                "Website": company_info.get("company_url", "N/A"),
                "SBIR Profile Link": company_info.get("sbir_url", "N/A")
            }
    else:
        logging.error(f"Failed to retrieve company info for UEI {uei}: {response.status_code}")
    return None

def get_award_info(company_name) -> list:
    """
    Fetch award information from the SBIR API using the company name.
    
    Arguments:
        company_name : str : Name of the company.
    Returns:
        list : List of awards associated with the company.
    """
    url = f"https://api.www.sbir.gov/public/api/awards?firm={company_name}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to retrieve award info for {company_name}: {response.status_code}")
    return []

def process_batch(uei_batch, batch_number, company_output_dir, awards_output_dir)-> None:
    """
    Process a batch of UEIs to fetch company and award information.

    Arguments:
        uei_batch : list : List of UEIs to process.
        batch_number : int : Current batch number.
        company_output_dir : str : Directory to save company information CSV.
        awards_output_dir : str : Directory to save award information CSV.
    """
    logging.info(f"Processing batch {batch_number} with {len(uei_batch)} UEIs")
    company_info_df = pd.DataFrame(columns=[
        "UEI", "Name", "Street Address", "City", "State", "Zip Code", "Website", "SBIR Profile Link"
    ])
    all_awards = []

    for uei in uei_batch:
        logging.info(f"Processing UEI: {uei}")
        company_info = get_company_info(uei)

        if company_info:
            company_info_df = pd.concat([company_info_df, pd.DataFrame([company_info])], ignore_index=True)
            company_name = company_info["Name"]
            award_data = get_award_info(company_name)
            for award in award_data:
                award["Company Name"] = company_name
                all_awards.append(award)

    company_batch_filename = os.path.join(company_output_dir, f"batch_{batch_number}.csv")
    company_info_df.to_csv(company_batch_filename, index=False)

    if all_awards:
        awards_df = pd.DataFrame(all_awards)
        awards_batch_filename = os.path.join(awards_output_dir, f"batch_{batch_number}.csv")
        awards_df.to_csv(awards_batch_filename, index=False)
    else:
        logging.warning(f"No award data found in batch {batch_number}")

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
        logging.info(f"Processing batch {batch_num + 1} with {len(uei_batch)} UEIs")
        process_batch(uei_batch, batch_num + 1, company_dir, awards_dir)

def main(input_file, output_path, batch_size) -> None:
    """
    Main function to set up logging, read input file, and process batches.

    Arguments:
        input_file : str : Path to input CSV file with UEIs.
        output_path : str : Directory to store output folders.
        batch_size : int : Number of UEIs to process per batch.
    """
    logging.basicConfig(filename=f'{output_path}/log/sbir_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
