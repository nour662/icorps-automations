import os
import requests
import pandas as pd
import logging
from argparse import ArgumentParser

def clean_location_dict(location) -> tuple:
    """
    Clean and extract address information from the location dictionary.

    Arguments:
        location (dict): Dictionary containing location information.
    Returns:
        tuple: Cleaned address information including address line 1, address line 2, city, state, zip code, and congressional code.
    """
    address_line1 = location.get("address_line1", "")
    address_line2 = location.get("address_line2", "")
    city = location.get("city_name", "")
    state = location.get("state_code", "")
    zip_code = location.get("zip", "")
    congressional_code = location.get("congressional_code", "")
    return address_line1, address_line2, city, state, zip_code, congressional_code

def get_company_info(recipient_ids) -> list:
    """
    Fetch company information from the USA Spending API using recipient IDs.

    Arguments:
        recipient_ids (list): List of recipient IDs.
    Returns:
        list: List of dictionaries containing company information including UEI, name, DUNS, address, and congressional code.
    """
    company_data_list = []
    for recipient_id in recipient_ids:
        recipient_url = f"https://api.usaspending.gov/api/v2/recipient/{recipient_id}/"
        response = requests.get(recipient_url)
        if response.status_code == 200:
            data = response.json()
            company_uei = data.get("uei", "")
            name = data.get("name", "")
            duns = data.get("duns", "")
            location = data.get("location", {})
            address_line1, address_line2, city, state, zip_code, congressional_code = clean_location_dict(location)

            company_data = {
                "uei": company_uei,
                "recipient_id": recipient_id,
                "name": name,
                "duns": duns,
                "address_line1": address_line1,
                "address_line2": address_line2,
                "city": city,
                "state": state,
                "zip": zip_code,
                "congressional_code": congressional_code
            }
            company_data_list.append(company_data)
        else:
            logging.warning(f"Failed to fetch company info for recipient ID {recipient_id}: {response.status_code}")
    return company_data_list

def get_data(response, all_data) -> list:
    """
    Process the response from the USA Spending API and extract award data.

    Arguments:
        response (requests.Response): Response object from the API request.
        all_data (list): List to store the extracted award data.
    Returns:
        list: Updated list of award data.
    """
    if response.status_code == 200:
        data = response.json()
        awards = data.get("results", [])
        if awards:
            all_data.extend(awards)
        return all_data
    else:
        logging.warning(f"Request failed with status code {response.status_code}")
        return None

def fetch_award_data(uei_list, header) -> tuple:
    """
    Fetch award data from the USA Spending API for a list of UEIs.

    Arguments:
        uei_list (list): List of UEIs to fetch award data for.
        header (dict): Headers for the API request.
    Returns:
        tuple: Two lists containing contract and grant data.
    """

    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    all_contract_data = []
    all_grant_data = []

    for uei in uei_list:
        if not pd.isna(uei):
            payload = {
                "filters": {
                    "recipient_search_text": [uei],
                    "award_type_codes": []
                },
                "fields": [
                    "Recipient Name", "Recipient UEI", "recipient_id", "Start Date", "End Date",
                    "Award Amount", "Awarding Agency", "Awarding Sub Agency", "Contract Award Type",
                    "Award Type", "Funding Agency", "Funding Sub Agency"
                ],
                "limit": 100
            }

            # Fetch contract data
            payload["filters"]["award_type_codes"] = ["A", "B", "C", "D"]
            response1 = requests.post(base_url, headers=header, json=payload)
            get_data(response1, all_contract_data)

            # Fetch grant data
            payload["filters"]["award_type_codes"] = ["02", "03", "04", "05"]
            response2 = requests.post(base_url, headers=header, json=payload)
            get_data(response2, all_grant_data)

            logging.info(f"Processed UEI: {uei}")
        else:
            logging.warning(f"Skipped invalid UEI: {uei}")

    return all_contract_data, all_grant_data

def process_in_batches(data_list, batch_size, process_function, *args, starting_batch=0) -> None:
    """
    Process a list of data in batches, optionally starting from a given batch index.

    Arguments:
        data_list (list): List of data to process.
        batch_size (int): Size of each batch.
        process_function (function): Function to process each batch.
        *args: Additional arguments to pass to the process_function.
        starting_batch (int): The batch index to start processing from.
    """
    total_batches = (len(data_list) + batch_size - 1) // batch_size
    for i in range(starting_batch * batch_size, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        process_function(batch, *args)


def save_data_in_batches(data, output_path, base_folder, batch_size) -> None:
    """
    Save data in batches to CSV files.

    Arguments:
        data (list): List of data to save.
        output_path (str): Directory to save the CSV files.
        base_folder (str): Base folder name for the output files.
        batch_size (int): Size of each batch.
    """
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        if not os.path.exists(os.path.join(output_path,base_folder)):
            os.makedirs(os.path.join(output_path,base_folder))
        batch_file = os.path.join(output_path, f"{base_folder}/batch_{i // batch_size + 1}.csv")
        pd.DataFrame(batch).to_csv(batch_file, index=False)
        logging.info(f"Saved batch to {batch_file}")

def main(input_file, output_path, batch_size, starting_batch) -> None:
    """
    Main function to read input file, fetch award and company data, and save results.
    
    Arguments:
        input_file (str): Path to the input CSV file containing UEIs.
        output_path (str): Directory to save the output CSV files.
    """
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logging.error(f"Failed to read input file: {e}")
        return

    if 'UEI' not in df.columns:
        logging.error("Input file must contain a 'UEI' column.")
        return

    ueis = df['UEI'].tolist()
    header = {"Content-Type": "application/json"}

    all_contract_data = []
    all_grant_data = []

    def fetch_award_batch(batch, header, contract_data, grant_data):
        contract_batch, grant_batch = fetch_award_data(batch, header)
        contract_data.extend(contract_batch)
        grant_data.extend(grant_batch)

    process_in_batches(ueis, batch_size, fetch_award_batch, header, all_contract_data, all_grant_data, starting_batch=starting_batch)

    # Save contract and grant data in batches
    save_data_in_batches(all_contract_data, output_path, "usas_batches/usas_contracts_batches", batch_size)
    save_data_in_batches(all_grant_data, output_path, "usas_batches/usas_grants_batches", batch_size)

    # Fetch company info in batches
    recipient_ids = list(set(
        pd.DataFrame(all_contract_data)["recipient_id"].tolist() +
        pd.DataFrame(all_grant_data)["recipient_id"].tolist()
    ))
    company_data = []

    def fetch_company_batch(batch, company_data):
        company_batch = get_company_info(batch)
        company_data.extend(company_batch)

    process_in_batches(recipient_ids, batch_size, fetch_company_batch, company_data)

    # Save company data in batches
    save_data_in_batches(company_data, output_path, "usas_batches/usas_company_info_batches", batch_size)

def parse_args():
    parser = ArgumentParser(description="Fetch award and company data for a list of UEIs.")
    parser.add_argument("--input_file", "-i", required=True, help="Path to the input CSV file containing UEIs.")
    parser.add_argument("--output_path", "-o", required=True, help="Directory to save the output CSV files.")
    parser.add_argument("--batch_size", "-b", required=False, default=10, help="Batch Size")
    parser.add_argument("--starting_batch", "-s", required=False, default=0, help="Starting Batch")
    parser.add_argument("--log_file", "-l", required=False, default="usas_log.txt", help="Log File")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(filename=f'{args.output_path}/log/usas_log.txt', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main(args.input_file, args.output_path,int(args.batch_size), int(args.starting_batch))
