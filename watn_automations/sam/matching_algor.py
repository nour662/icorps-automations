import pandas as pd
import re
from rapidfuzz import process, fuzz
import logging
from argparse import ArgumentParser
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_company_name(name):
    if pd.isna(name):
        return ''
    name = re.sub(r"[^\w\s]", "", name.lower().strip())
    name = name.replace("corporation", "corp").replace("incorporated", "inc")
    return name

def match_companies(sam_company, sf_companies):
    match = process.extractOne(sam_company, sf_companies, scorer=fuzz.ratio)
    return match[0] if match and match[1] > 80 else None  # Threshold set to 80

def match_contacts(sam_contacts, sf_contacts):
    return list(set(sam_contacts) & set(sf_contacts))

def clean_masterlist(df):
    logging.info("Cleaning masterlist...")
    try:
        df["Full Name"] = df["First Name"].fillna('') + " " + df["Last Name"].fillna('')
        df.drop(columns=["First Name", "Last Name"], inplace=True)
        df["Regional Cohort Date"] = pd.to_datetime(df["Regional Cohort Date"], errors="coerce")
        grouped = (
            df.groupby("Company")
            .agg({"Full Name": lambda x: list(set(x))})  # Remove duplicate names
            .reset_index()
        )
        grouped = grouped.rename(columns={"Company": "sf_company", "Full Name": "sf_contacts"})
        grouped["sf_company"] = grouped["sf_company"].apply(clean_company_name)
        return grouped
    except Exception as e:
        logging.error(f"Error in cleaning masterlist: {e}")
        raise

def clean_sam(df):
    logging.info("Cleaning SAM dataset...")

    def extract_name(name):
        if pd.isna(name):
            return None
        pattern = r"^([A-Za-z]+)\s?([A-Za-z]?.)?\s([A-Za-z]+)"
        match = re.match(pattern, name.strip())
        if match:
            first_name = match.group(1)
            last_name = match.group(3)
            return f"{first_name} {last_name}" if first_name and last_name else None
        return None

    df = df.rename(columns={"legal_name": "sam_company"})
    df["sam_company"] = df["sam_company"].apply(clean_company_name)
    df["sam_contacts"] = df.apply(
        lambda row: list(set(filter(None, [
            extract_name(row.get("contact1")),
            extract_name(row.get("contact2"))
        ]))),
        axis=1
    )
    return df

def match_datasets(master_df, sam_df):
    logging.info("Matching datasets...")

    matched = pd.merge(sam_df, master_df, left_on="sam_company", right_on="sf_company", how="inner")

    unmatched_sam = sam_df[~sam_df["sam_company"].isin(matched["sam_company"])]
    sf_company_list = master_df["sf_company"].tolist()
    unmatched_sam["matched_company"] = unmatched_sam["sam_company"].apply(lambda x: match_companies(x, sf_company_list))

    fuzzy_matched = unmatched_sam.merge(master_df, left_on="matched_company", right_on="sf_company", how="inner")
    all_matches = pd.concat([matched, fuzzy_matched], ignore_index=True)

    all_matches["contact_overlap"] = all_matches.apply(
        lambda row: match_contacts(row["sam_contacts"], row["sf_contacts"]),
        axis=1
    )

    final_matches = all_matches[all_matches["contact_overlap"].str.len() > 0]

    return final_matches



def main(masterlist_path, sam_data_path):
    masterlist = pd.read_csv("../inputs/icorps_masterlist.csv")
    sam_data = pd.read_csv("training.csv")

    masterlist_cleaned = clean_masterlist(masterlist)
    sam_data_cleaned = clean_sam(sam_data)

    results = match_datasets(masterlist_cleaned, sam_data_cleaned)

    results.to_csv("matched_results.csv", index=False)
    logging.info("Matching complete. Results saved to matched_results.csv")



def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--masterlist-path", "-m", required=False, help="Path to I-Corps Masterlist")
    parser.add_argument("--sam_data_path", "-s", required=True, help="Path to output data from SAM.gov")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.masterlist_path, args.sam_data_path)
