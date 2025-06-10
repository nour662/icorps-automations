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

def clean_input(df) -> pd.DataFrame:
    """
    Cleans the input DataFrame by combining first and last names into a single column.
    Also groups by company name and aggregates contacts.

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
                "Website": lambda x: x if "Website" in df.columns else None
            })
            .reset_index()
        )

        grouped = grouped.rename(columns={"Company": "input_company", "Name": "input_contacts",  "Website": "input_url"})
        
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
    df = df.rename(columns={"legal_name": "sam_company", "contacts": "sam_contacts" , "entity_url": "sam_url"})
    df["sam_contacts"] = df["sam_contacts"].apply(
        lambda x: eval(x) if isinstance(x, str) else ([] if pd.isna(x) else x)
    )

    return df

def cleaned_dfs(input_df, sam_df) -> tuple:
    """
    Cleans and modifes the input and SAM DataFrames for further processing in place.
    
    Arguments:
        input_df (DataFrame): The input DataFrame containing company information.
        sam_df (DataFrame): The SAM DataFrame containing company information from SAM.gov. 
    """
    logging.info("Cleaning original input file...")
    try:
        if {"First Name", "Last Name"}.issubset(input_df.columns):
            input_df["Name"] = input_df["First Name"].fillna('') + " " + input_df["Last Name"].fillna('')
            input_df.drop(columns=["First Name", "Last Name"], inplace=True)

        grouped = (
            input_df.groupby("Company")
            .agg({
                "Name": lambda x: list(set(x)),
                "Website": lambda x: x if "Website" in input_df.columns else None
            })
            .reset_index()
        )

        cleaned_input_df = grouped.rename(columns={"Company": "input_company", "Name": "input_contacts",  "Website": "input_url"})
        
        logging.info("Cleaning SAM dataset...")
        sam_df = sam_df.rename(columns={"legal_name": "sam_company", "contacts": "sam_contacts" , "entity_url": "sam_url"})
        sam_df["sam_contacts"] = sam_df["sam_contacts"].apply(
            lambda x: eval(x) if isinstance(x, str) else ([] if pd.isna(x) else x)
        )
        
        return cleaned_input_df, sam_df
        
    except Exception as e:
        logging.error(f"Error in cleaning input data: {e}")
        raise
    
    

    
    

def join_dfs(input_df, sam_df) -> pd.DataFrame:
    """
    Joins the input DataFrame with the SAM DataFrame on either company names 
    or UEI depending on the Keyword Column in the input DataFrame.
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

    merged_name = pd.merge(
        input_df,
        sam_df,
        left_on="input_company",
        right_on="keyword",
        how="outer",
        suffixes=("_input", "_sam")
    )
    merged_name["match_type"] = "company"

    if 'UEI' in input_df.columns and 'num_uei' in sam_df.columns:
        merged_uei = pd.merge(
            input_df,
            sam_df,
            left_on="UEI",
            right_on="keyword",
            how="outer",
            suffixes=("_input", "_sam")
        )
        
        merged_uei["match_type"] = "uei"
        
        merged_df = pd.concat([merged_name, merged_uei], ignore_index=True).drop_duplicates()
    else:
        merged_df = merged_name

    keep_cols = [
        col for col in merged_df.columns
        if col.startswith("input") or col.startswith("sam") or col in {"keyword", "num_uei", "match_type"}
    ]
    merged_df = merged_df[keep_cols]

    merged_df = merged_df.dropna(subset=["input_company", "sam_company"], how="all")

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
        sam_company = row.get("sam_company", "")
        input_contacts = row.get("input_contacts", [])
        sam_contacts = row.get("sam_contacts", [])
        sam_url = row.get("sam_url", "") 
        input_url = row.get("input_url", "")

        input_company = clean_company_name(input_company)
        sam_company = clean_company_name(sam_company)

        company_score = fuzz.ratio(input_company, sam_company)
        
        website_score = fuzz.ratio(str(input_url), str(sam_url))

        matched_contacts, contact_score = match_contacts(sam_contacts, input_contacts)
        overall_score = round((0.65 * company_score + 0.15 * website_score + 0.2 * contact_score), 2)

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
            "overall_score": overall_score,
            "match_type": row.get("match_type", "company")
        })

    return pd.DataFrame(results)

def merge_final_output(input_df, results_df, input_path) -> None:
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

    merged.to_csv(input_path, index=False)
    logging.info(f"Final merged output saved to {input_path}")

def main(input_path, data_path, output_path) -> None:
    """
    Main function to execute the matching algorithm.

    Arguments:
        input_path : (str) Path to the original input data.
        data_path : (str) Path to the scraped data from SAM.gov.
    """

    logging.info("Starting matching process...")
    
    input_df = pd.read_csv(input_path)
    sam_df = pd.read_csv(data_path)

    if input_df.empty:
        logging.error("Input file is empty. Please check the file.")
        return

    input_df_cleaned,sam_df_cleaned = cleaned_dfs(input_df, sam_df)

    merged_df = join_dfs(input_df_cleaned, sam_df_cleaned)
    results = find_matches(merged_df)
    
    if not results.empty:
        results['match_priority'] = results['match_type'].map({'uei': 0, 'company': 1})
        best_matches = results.sort_values('overall_score', ascending=False).groupby('input_company').head(1)
        merge_final_output(input_df, best_matches, input_path)
    else:
        logging.warning("No matches found with given threshold. Skipping final merge.")

def parse_args(arglist) -> ArgumentParser:
    """
    Parses command line arguments.
    Arguments:
        arglist : (list) List of command line arguments.
    Returns:
        Namespace : Parsed command lin∂e arguments.
    """
    parser = ArgumentParser()
    parser.add_argument("--input_path", "-i", required=True, help="Path to original input data")
    parser.add_argument("--data_path", "-d", required=True, help="Path to scraped data from SAM.gov")
    parser.add_argument("--output_path", "-o", required=True, help="Path to log file")
    parser.add_argument("--log_file", "-l", required=False, default="log/sam_log.txt", help = "Log File")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    logging.basicConfig(filename=f'{args.output_path}/{args.log_file}', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    main(args.input_path, args.data_path, args.output_path)


