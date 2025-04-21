import os
import requests
import pandas as pd
import logging
import argparse


def clean_location_dict(location):
    address_line1 = location.get("address_line1", "")
    address_line2 = location.get("address_line2", "")
    city = location.get("city_name", "")
    state = location.get("state_code", "")
    zip_code = location.get("zip", "")
    congressional_code = location.get("congressional_code", "")
    return address_line1, address_line2, city, state, zip_code, congressional_code


def get_company_info(recipient_ids):
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


def get_data(response, all_data):
    if response.status_code == 200:
        data = response.json()
        awards = data.get("results", [])
        if awards:
            all_data.extend(awards)
        return all_data
    else:
        logging.warning(f"Request failed with status code {response.status_code}")
        return None


def fetch_award_data(uei_list, header):

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


def process_in_batches(data_list, batch_size, process_function, *args):
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        process_function(batch, *args)


def save_data_in_batches(data, output_path, base_folder, batch_size):
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        if not os.path.exists(os.path.join(output_path,base_folder)):
            os.makedirs(os.path.join(output_path,base_folder))
        batch_file = os.path.join(output_path, f"{base_folder}/batch_{i // batch_size + 1}.csv")
        pd.DataFrame(batch).to_csv(batch_file, index=False)
        logging.info(f"Saved batch to {batch_file}")


def main(input_file, output_path):
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

    batch_size = 10
    all_contract_data = []
    all_grant_data = []

    def fetch_award_batch(batch, header, contract_data, grant_data):
        contract_batch, grant_batch = fetch_award_data(batch, header)
        contract_data.extend(contract_batch)
        grant_data.extend(grant_batch)

    process_in_batches(ueis, batch_size, fetch_award_batch, header, all_contract_data, all_grant_data)

    # Save contract and grant data in batches
    save_data_in_batches(all_contract_data, output_path, "usas_contracts", batch_size)
    save_data_in_batches(all_grant_data, output_path, "usas_grants", batch_size)

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
    save_data_in_batches(company_data, output_path, "usas_company_info", batch_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch award and company data for a list of UEIs.")
    parser.add_argument("--input_file", "-i", help="Path to the input CSV file containing UEIs.")
    parser.add_argument("--output_path", "-o", help="Directory to save the output CSV files.")
    args = parser.parse_args()

    logging.basicConfig(filename=f'{args.output_path}/../log/usas_log.txt',level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main(args.input_file, args.output_path)
