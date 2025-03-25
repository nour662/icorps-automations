import argparse
import requests
import csv
import re

def get_firm_info_by_uei(uei):
    BASE_URL = "https://api.www.sbir.gov/public/api/firm"
    response = requests.get(BASE_URL, params={"uei": uei})
    
    if response.status_code == 200:
        firm_data = response.json()
        return firm_data if firm_data else None
    return None

def get_awards_by_firm_name(firm_name):
    BASE_URL = "https://api.www.sbir.gov/public/api/awards"
    response = requests.get(BASE_URL, params={"firm": firm_name})
    
    return response.json() if response.status_code == 200 else None

def extract_company_info(firm_data):
    firm_data = firm_data[0]
    return {
        "Company Name": firm_data.get("company_name"),
        "UEI": firm_data.get("uei"),
        "DUNS": firm_data.get("duns"),
        "SBIR Profile": firm_data.get("sbir_url"),
        "Number of Employees": firm_data.get("number_employees"),
        "Women Owned": firm_data.get("women_owned"),
        "Company URL": firm_data.get("company_url"),
        "Address": f"{firm_data.get('address1', '')} {firm_data.get('address2', '')}".strip(),
        "City": firm_data.get("city"),
        "State": firm_data.get("state"),
        "ZIP Code": firm_data.get("zip"),
    }

def extract_funding_info(awards, uei):
    return [
        {
            "Company Name": award.get('firm_name'),
            "UEI": award.get("uei"),
            "Award Title": award.get("award_title"),
            "Agency": award.get("agency"),
            "Branch": award.get("branch"),
            "Phase": award.get("phase"),
            "Award Year": award.get("award_year"),
            "Award Amount": award.get("award_amount"),
            "Contract Number": award.get("contract"),
            "Proposal Award Date": award.get("proposal_award_date"),
            "Contract End Date": award.get("contract_end_date"),
            "Award Link": f'https://www.sbir.gov/awards/{award.get("award_link")}'
        }
        for award in awards if award.get("uei") == uei
    ]

def save_to_csv(filename, data_list):
    if not data_list:
        print(f"No data to save for {filename}")
        return

    keys = data_list[0].keys()  
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)
    print(f"Data saved to {filename}")

def clean_firm_name(firm_name):
    cleaned_name = re.sub(r'\b(Inc|LLC|Corp|Ltd|Co|LLP|Ltd.)\b', '', firm_name, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'[^A-Za-z0-9\s]', '', cleaned_name)
    return cleaned_name.strip()

def main(input_file, output_file):
    with open(input_file, mode='r', newline='') as infile:
        reader = csv.DictReader(infile)
        uei_list = [row['UEI'] for row in reader]
    
    all_company_info = []
    all_funding_info = []

    for uei in uei_list:
        print(f"Processing UEI: {uei}")

        firm_info = get_firm_info_by_uei(uei)
        if firm_info:
            company_info = extract_company_info(firm_info)

            firm_name = company_info["Company Name"]
            cleaned_firm_name = clean_firm_name(firm_name)
            awards = get_awards_by_firm_name(cleaned_firm_name)

            funding_info = extract_funding_info(awards, uei) if awards else []

            all_company_info.append(company_info)
            all_funding_info.extend(funding_info)

        else:
            print(f"No company found for UEI: {uei}")

    save_to_csv(output_file + "_company_info.csv", all_company_info)
    save_to_csv(output_file + "_funding_info.csv", all_funding_info)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process UEIs and get data from SBIR APIs.")
    parser.add_argument('input_file', type=str, help="Path to the input CSV file containing UEIs.")
    parser.add_argument('output_file', type=str, help="Base path for the output CSV files.")
    
    args = parser.parse_args()

    main(args.input_file, args.output_file)
