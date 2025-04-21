
import pandas as pd
import requests
import re
import logging
from argparse import ArgumentParser


def get_firm_info_by_duns(duns_number):
    BASE_URL = "https://api.www.sbir.gov/public/api/firm"

    if not duns_number: 
        return None
    
    params = {'duns': duns_number}
    
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        firm_data = response.json()
        return firm_data[0] if firm_data else None
    return None

def main(input_file, output_path):
    logging.basicConfig(
        filename=f'{output_path}/log/duns_search_log.txt',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    df_original = pd.read_csv(input_file, dtype=str)

    if "DUNS" not in df_original.columns:
        logging.error("DUNS column not found in the input file.")
        logging.error("Skipping DUNS search.")
        return

    if "UEI" not in df_original.columns:
        df_original["UEI"] = None
    
    df_filtered = df_original[df_original["DUNS"].notnull() & df_original["UEI"].isnull()].copy()

    for index, row in df_filtered.iterrows():
        company = row.get('Company')
        duns_number = row.get('DUNS')

        logging.info(f"Processing {company} with DUNS: {duns_number}")

        firm_info = get_firm_info_by_duns(duns_number)

        if firm_info:
            df_filtered.at[index, 'UEI'] = firm_info.get('uei', None)
        else:
            logging.error(f"No data found for DUNS: {duns_number}")

    df_original.update(df_filtered)

    df_original.to_csv(input_file, index=False)
    logging.info(f"Data updated in original file: {input_file}")


def parse_arguments():
    parser = ArgumentParser(description="Process DUNS numbers and fetch firm data.")
    parser.add_argument('--input_file', '-i', type=str, help='Input CSV file with DUNS numbers')
    parser.add_argument('--output_path', '-o', type=str, help='Output path file to save results')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    main(args.input_file, args.output_path)
