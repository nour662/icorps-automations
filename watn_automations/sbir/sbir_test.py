import requests
import pandas as pd
import os
import logging

AWARD_FIELDS = [
    "Company Name", "award_title", "agency", "branch", "phase", "program",
    "agency_tracking_number", "contract", "proposal_award_date", "contract_end_date",
    "solicitation_number", "solicitation_year", "topic_code", "award_year",
    "award_amount", "award_link"
]

COMPANY_FIELDS = ["duns","number_employees"]

def get_company_info(uei):
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
            }, company_info
    logging.error(f"Failed to retrieve company info for UEI {uei}: {response.status_code}")
    return None, None

def get_award_info(company_name):
    url = f"https://api.www.sbir.gov/public/api/awards?firm={company_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to retrieve award info for {company_name}: {response.status_code}")
    return []

def main():
    input_file = "watn_automations\sam\sample_input.csv"
    output_path = "watn_automations\sbir\outputs"
    
    company_dir = os.path.join(output_path, "sbir_batches/sbir_company_info_batches")
    awards_dir = os.path.join(output_path, "sbir_batches/sbir_awards_batches")
    os.makedirs(company_dir, exist_ok=True)
    os.makedirs(awards_dir, exist_ok=True)

    logging.basicConfig(
        filename=os.path.join(output_path, "log", "sbir_log.txt"),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    df = pd.read_csv(input_file)
    uei_list = df['UEI'].dropna().tolist()

    company_info_records = []
    award_core_records = []
    award_company_records = []

    for uei in uei_list:
        logging.info(f"Processing UEI: {uei}")
        company_structured, company_raw = get_company_info(uei)
        if not company_structured or not company_raw:
            logging.warning(f"No company data found for UEI: {uei}")
            continue

        company_name = company_structured["Name"]
        print(company_structured)
        

        awards = get_award_info(company_name)
        for award in awards:
            award["Company Name"] = company_name
            core_record = {field: award.get(field, "") for field in AWARD_FIELDS}
            award_core_records.append(core_record)

            company_structured.update({field: award.get(field, company_raw.get(field, "")) for field in COMPANY_FIELDS})
            print(company_structured)
            
        company_info_records.append(company_structured)
        print(company_info_records)

    pd.DataFrame(company_info_records).to_csv(os.path.join(output_path, "sbir_company_info.csv"), index=False)
    pd.DataFrame(award_core_records).to_csv(os.path.join(output_path, "sbir_funding_info.csv"), index=False)

if __name__ == "__main__":
    main()