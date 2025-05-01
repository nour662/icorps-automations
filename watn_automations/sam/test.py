import pandas as pd
import re
from rapidfuzz import fuzz
import logging
from argparse import ArgumentParser
import sys

# 60: company 30:website  10:contacts split
# 62: company 25:website  10:contacts split
def clean_company_name(name) -> str:
    """
    Cleans the company name by removing special characters and standardizing common terms.

    Aruments:
        name : (str) The company name to be cleaned.
    Returns:
        str : The cleaned company name.
    """
    if pd.isna(name):
        return ''
    name = re.sub(r"[^\w\s]", "", name.lower().strip())
    name = name.replace("corporation", "corp").replace("incorporated", "inc")

    suffixes = [" inc", " llc", " ltd", " corp", " co", " company", " pllc", " lp", " llp"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()

def match_contacts(sam_contacts, input_contacts) -> tuple:
    """
    Matches contacts from SAM dataset with input contacts using fuzzy string matching.

    Arguments:
        sam_contacts : (list) List of contacts from SAM dataset.
        input_contacts : (list) List of contacts from input dataset.
    Returns:
        tuple : A tuple containing the best match and its score.
    """
    logging.info("Matching contacts...")
    sam_contacts = sam_contacts if isinstance(sam_contacts, list) else []
    input_contacts = input_contacts if isinstance(input_contacts, list) else []

    highest_score = 0
    best_match = None

    for sam_contact in sam_contacts:
        for input_contact in input_contacts:
            score = fuzz.ratio(sam_contact.lower(), input_contact.lower())
            if score > highest_score:
                highest_score = score
                best_match = sam_contact

    return [best_match] if best_match else [], highest_score

def website_is_present(df):
    if 'Website' not in df.columns:
        return None
    else:
        return df["Website"]
    
def clean_input(df) -> pd.DataFrame:
    """
    Cleans the input DataFrame by combining first and last names into a single column.
    Also groups by company name website and aggregates contacts.

    Arguments:
        df : (DataFrame) The input DataFrame to be cleaned.
    Returns:
        DataFrame : The cleaned DataFrame with company names and aggregated contacts.
    """
    logging.info("Cleaning original input file...")
    try:
        if {"First Name", "Last Name"}.issubset(df.columns):
            df["Name"] = df["First Name"].fillna('') + " " + df["Last Name"].fillna('')
            df.drop(columns=["First Name", "Last Name"], inplace=True)
            
        grouped = (
            df.groupby("Company")
            .agg({
                "Name": lambda x: list(set(x)),
                "Website": lambda x: website_is_present(x)})
            .reset_index()
        )
            
        grouped = grouped.rename(columns={"Company": "input_company", "Name": "input_contacts", "Website": "input_website"})
        return grouped
    except Exception as e:
        logging.error(f"Error in cleaning input data: {e}")
        raise

def clean_sam(df) -> pd.DataFrame:
    """
    Cleans the SAM DataFrame by renaming columns and converting contacts to lists.
    Also handles missing values.

    Arguments:
        df : (DataFrame) The SAM DataFrame to be cleaned.
    Returns:
        DataFrame : The cleaned SAM DataFrame with standardized column names and contact lists.
    """

    logging.info("Cleaning SAM dataset...")
    df = df.rename(columns={"legal_name": "sam_company", "contacts": "sam_contacts"})
    df["sam_contacts"] = df["sam_contacts"].apply(
        lambda x: eval(x) if isinstance(x, str) else ([] if pd.isna(x) else x)
    )
    return df

def join_dfs(input_df, sam_df) -> pd.DataFrame:
    """
    Joins the input DataFrame with the SAM DataFrame on company names.
    Also drops rows with missing values in the joined DataFrame.

    Arguments:
        input_df : (DataFrame) The cleaned input DataFrame.
        sam_df : (DataFrame) The cleaned SAM DataFrame.
    Returns:
        DataFrame : The merged DataFrame with company names and contacts.
    """
    logging.info("Joining datasets...")
    if "keyword" not in sam_df.columns or "input_company" not in input_df.columns:
        logging.error("Required columns 'keyword' or 'input_company' are missing.")
        return pd.DataFrame()

    merged_df = pd.merge(
        input_df,
        sam_df,
        left_on="input_company",
        right_on="keyword",
        how="outer",
        suffixes=("_input", "_sam")
    )

    merged_df = merged_df.dropna(subset=["input_company", "sam_company"])
    return merged_df

def find_matches(merged_df, threshold=80) -> pd.DataFrame:
    """
    Finds matches between input and SAM companies using fuzzy string matching.

    Arguments:
        merged_df : (DataFrame) The merged DataFrame containing input and SAM companies.
        threshold : (int) The score threshold for considering a match.
    Returns:
        DataFrame : A DataFrame containing the matched results.
    """

    logging.info("Scoring matches within joined DataFrame...")

    results = []

    for _, row in merged_df.iterrows():
        input_company = row.get("input_company", "")
        print(input_company)
        sam_company = row.get("sam_company", "")
        input_contacts = row.get("input_contacts", [])
        sam_contacts = row.get("sam_contacts", [])
        input_website = row.get("input_website", "")
        print("input website: ", input_website)
        sam_entity_url = row.get("sam_entity_url", "")
        print("Sam entity url: ", sam_entity_url)
        
        
        input_company = clean_company_name(input_company)
        sam_company = clean_company_name(sam_company)

        company_score = fuzz.ratio(input_company, sam_company)
        
        if input_website == None:
            website_score = 0
        else: 
            website_score = fuzz.ratio(input_website, sam_entity_url)
        
        

        matched_contacts, contact_score = match_contacts(sam_contacts, input_contacts)
        overall_score = round((0.65 * company_score + 0.25 * website_score + 0.1 * contact_score), 2)
        print(overall_score)
        if overall_score < threshold:
            continue
        
        results.append({
            "keyword": row.get("keyword", ""),
            "uei" : row.get("num_uei", ""),
            "input_company": input_company,
            "sam_company": sam_company,
            "company_score": company_score,
            "matched_contacts": matched_contacts,
            "contact_score": round(contact_score, 2),
            "input_website": input_website,
            "sam_entity_url": sam_entity_url,
            "website_score": website_score,
            "overall_score": overall_score
        })

    return pd.DataFrame(results)

def merge_final_output(input_df, results_df, output_path) -> None:
    """
    Merges the final output with UEIs and saves the result to a CSV file.

    Arguments:
        input_df : (DataFrame) The original input DataFrame.
        results_df : (DataFrame) The DataFrame containing matched results.
        output_path : (str) The path to save the final output CSV file.
    """
    logging.info("Merging final output with UEIs…")

    ueis = results_df[['keyword', 'uei']].rename(columns={'uei': 'uei_new'})

    merged = pd.merge(
        input_df,
        ueis,
        left_on="Company",
        right_on="keyword",
        how="left"
    )

    if 'UEI' in merged.columns:
        merged['UEI'] = merged['uei_new'].combine_first(merged['UEI'])
    else:
        merged['UEI'] = merged['uei_new']

    drop_cols = [col for col in ['keyword', 'uei_new'] if col in merged.columns]
    merged.drop(columns=drop_cols, inplace=True)


    output_file = f"{output_path}/post_sam_matching.csv"
    
    merged.to_csv(output_file, index=False)
    logging.info(f"Final merged output saved to {output_file}")

def main() -> None:
    """
    Main function to execute the matching algorithm.

    Arguments:
        input_path : (str) Path to the original input data.
        data_path : (str) Path to the scraped data from SAM.gov.
        output_path : (str) Path to the output folder.
    """

    logging.info("Starting matching process...")

    input_df = pd.read_csv("watn_automations\sam\sample_input.csv")
    sam_df = pd.read_csv("watn_automations\sam\sampl_sam.csv")

    if input_df.empty:
        logging.error("Input file is empty. Please check the file.")
        return

    input_df_cleaned = clean_input(input_df)
    sam_df_cleaned = clean_sam(sam_df)

    merged_df = join_dfs(input_df_cleaned, sam_df_cleaned)
    results = find_matches(merged_df)

    best_matches = results.sort_values('overall_score', ascending=False).groupby('input_company').head(1)

    # merge_final_output(input_df , best_matches, output_path)
    # logging.info("Matching complete. Results saved to matched_results.csv in cleaned_output folder")

# def parse_args(arglist) -> ArgumentParser:
#     """
#     Parses command line arguments.
#     Arguments:
#         arglist : (list) List of command line arguments.
#     Returns:
#         Namespace : Parsed command lin∂e arguments.
#     """
#     parser = ArgumentParser()
#     parser.add_argument("--input_path", "-i", required=True, help="Path to original input data")
#     parser.add_argument("--data_path", "-d", required=True, help="Path to scraped data from SAM.gov")
#     parser.add_argument("--output_path", "-o", required=True, help="Path to output folder")
#     parser.add_argument("--log_file", "-l", required=False, default="log/sam_log.txt", help = "Log File")
#     return parser.parse_args(arglist)

if __name__ == "__main__":
    logging.basicConfig(filename= "log.txt", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    main()


