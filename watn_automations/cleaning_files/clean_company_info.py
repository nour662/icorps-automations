import pandas as pd
from argparse import ArgumentParser
import pandas as pd
import re
import col_converts
import os

def parse_address(address):
    address_regex = re.compile(
    r"""^(?P<street>.+?),(?:(?P<street2>[^,]+),)?\s*
        (?P<city>[A-Za-z\s]+),\s*
        (?P<state>[A-Z]{2}|[A-Za-z\s]+),\s*
        (?P<zip_code>\d{5}(?:-\d{4})?),\s*
        (?P<country>[A-Za-z\s]+)$""",
    re.VERBOSE
)
    match = address_regex.match(address.strip())
    if match:
        result = match.groupdict()
        if result.get("street2"):
            result["street"] = result["street"] + ", " + result["street2"]
        result.pop("street2", None)
        result["zip_code"] = result["zip_code"][:5]
        return result
    else:
        return {
            "street": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "country": None
        }

def convert_congresional_district(district):
    if pd.isna(district):
        return None

    state_abbr = col_converts.get_state_abbreviations() 
    
    parts = district.split()
    if len(parts) < 2:
        return None  


    state_name = " ".join(parts[:-1])
    district_number = parts[-1] 

    state_abbr = state_abbr.get(state_name)
    if not state_abbr:
        return None

    return f"{state_abbr}-{district_number.zfill(2)}"

def clean_legal_name(name):
    name = re.sub(r"[^\w\s]", "", name)  
    name = re.sub(r"\s+", " ", name.strip())  
    name = name.title() 

    if not isinstance(name, str) or not name.strip():
        return None

    if name.lower().endswith("llc"):
        name = re.sub(r"\s*llc$", ", LLC", name, flags=re.IGNORECASE)
    elif name.lower().endswith("inc"):
        name = re.sub(r"inc$", "Inc.", name, flags=re.IGNORECASE)
    elif name.lower().endswith("corp"):
        name = re.sub(r"corp$", "Corp.", name, flags=re.IGNORECASE)

    return name

def save_to_csv(df, file_path):
    try:
        df.to_csv(file_path, index=False)
        print(f"DataFrame saved to {file_path}")
    except Exception as e:
        print(f"Error saving DataFrame to {file_path}: {e}")

def change_col_names(df, col_mapping):
    for col in df.columns:
        if col in col_mapping.keys():
            new_col = col_mapping[col]
            df.rename(columns={col: new_col}, inplace=True)
        else:
            df.drop(columns=[col], inplace=True)
    return df

def clean_revenue(revenue):
    if pd.isna(revenue):
        return None
    full_revenue = revenue * 1_000_000

    if full_revenue < 100_000:
        return "< $100,000"
    elif 100_000 <= full_revenue < 1_000_000:
        return "$100,000 to $1 Million"
    elif 1_000_000 <= full_revenue < 10_000_000:
        return "$1 Million to $10 Million"
    elif 10_000_000 <= full_revenue < 100_000_000:
        return "$10 Million to $100 Million"
    else:
        return "> $100 Million"

def clean_sam(ueis, sam_df):

    parsed_physical_addresses = sam_df["physical_address"].apply(parse_address)
    sam_df["street"] = parsed_physical_addresses.apply(lambda x: x["street"])
    sam_df["city"] = parsed_physical_addresses.apply(lambda x: x["city"])
    sam_df["state"] = parsed_physical_addresses.apply(lambda x: x["state"])
    sam_df["zip_code"] = parsed_physical_addresses.apply(lambda x: x["zip_code"])
    sam_df["country"] = parsed_physical_addresses.apply(lambda x: x["country"])

    sam_df["legal_name"] = sam_df["legal_name"].apply(lambda x: clean_legal_name(x) if pd.notna(x) else None)

    incorporation_parts = sam_df["state_country_incorporation"].str.split(",", expand=True)
    sam_df["incorporation_state"] = incorporation_parts[0].str.strip()
    sam_df["incorporation_country"] = incorporation_parts[1].str.strip() if incorporation_parts.shape[1] > 1 else None

    sam_df["congressional_district"] = sam_df["congressional_district"].apply(convert_congresional_district)

    col_conversions = col_converts.get_sam_compinfo_col_mapping()

    sam_df = change_col_names(sam_df, col_conversions)

    sam_df = sam_df[sam_df["UEI"].isin(ueis)]
    sam_df = sam_df.replace("(blank)", "", regex=False)
    
    sam_df = sam_df.loc[sam_df["UEI"].drop_duplicates(keep="first").index]

    return sam_df

def clean_usas(usas_df):
    col_conversions = col_converts.get_usas_compinfo_col_mapping()

    usas_df["congressional_district"] = usas_df["state"] + "-" + usas_df["congressional_code"].astype(str).str.zfill(2)
    usas_df["duns"] = usas_df["duns"].apply(lambda x: str(x).split(".")[0].zfill(9) if pd.notna(x) else None)

    usas_df = change_col_names(usas_df, col_conversions)
    usas_df = usas_df.loc[usas_df["UEI"].drop_duplicates(keep="first").index]

    return usas_df

def clean_sbir(sbir_df):
    col_conversions = col_converts.get_sbir_compinfo_col_mapping()


    sbir_df["Street Address"] = sbir_df["Street Address"].apply(lambda x: str(x).split(",")[0].title() if pd.notna(x) else None)
    sbir_df["duns"] = sbir_df["duns"].apply(lambda x: str(x).split(".")[0].zfill(9) if pd.notna(x) else None)
    sbir_df["City"] = sbir_df["City"].apply(lambda x: str(x).split(",")[0].title() if pd.notna(x) else None)
    
    state_abbr_to_full = {v: k for k, v in col_converts.get_state_abbreviations().items()}
    sbir_df["State"] = sbir_df["State"].apply(lambda x: state_abbr_to_full.get(x.upper(), x).title() if pd.notna(x) else None)
    sbir_df["Zip Code"] = sbir_df["Zip Code"].apply(lambda x: str(x)[:5] if pd.notna(x) else None)

    sbir_df = change_col_names(sbir_df, col_conversions)

    sbir_df = sbir_df.loc[sbir_df["UEI"].drop_duplicates(keep="first").index]

    return sbir_df

def clean_pitchbook(pb_df, pb_matches):
    col_conversions = col_converts.get_pb_compinfo_col_mapping()

    pb_df = pb_df.merge(pb_matches[["Company", "Firm Name from PitchBook"]], how="right", left_on="company", right_on="Firm Name from PitchBook")
    pb_df.drop_duplicates(subset=["company"], inplace=True)
    pb_df = pb_df[pb_df["company"].notna()]

    pb_df = pb_df.drop(columns=["Firm Name from PitchBook", "company"])

    pb_df = pb_df.loc[pb_df["Company"].drop_duplicates(keep="first").index]

    state_abbr_to_full = {v: k for k, v in col_converts.get_state_abbreviations().items()}

    pb_df["legalName"] = pb_df["legalName"].apply(lambda x: clean_legal_name(x) if pd.notna(x) else None)


    pb_df["hqCity"] = pb_df["hqLocation"].apply(
        lambda x: str(x).split(",")[0].title() if pd.notna(x) and len(str(x).split(",")) == 2 else None
    )
    pb_df["hqState"] = pb_df["hqLocation"].apply(
        lambda x: state_abbr_to_full.get(str(x).split(",")[-1].strip().upper(), str(x).split(",")[-1].strip()).title()
        if pd.notna(x) and len(str(x).split(",")) == 2 else None
    )
    pb_df["Country"] = pb_df["hqState"].apply(
        lambda state: "United States" if pd.notna(state) else None
    )
    pb_df["revenue"] = pb_df["revenue"].apply(
        lambda x: clean_revenue(float(str(x).split(" ")[0].replace("$", "").replace(",", ""))) if pd.notna(x) else None
    )

    pb_df["employees"] = pb_df["employees"].apply(
        lambda x: str(int(float(x))) if pd.notna(x) else None
    )

    pb_df["yearFounded"] = pb_df["yearFounded"].apply(
        lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '', 1).isdigit() and float(x).is_integer() else None
    )

    pb_df = change_col_names(pb_df, col_conversions)

    return pb_df

def main(input_folder , root_tag):
    input_file = os.path.join(input_folder, "inputs", f"{root_tag}.csv")
    input_df = pd.read_csv(input_file)

    ueis = input_df["UEI"].dropna().tolist()
    cleaned_output_dir = os.path.join(input_folder, "cleaned_outputs", "company_info")
    os.makedirs(cleaned_output_dir, exist_ok=True)

    sources = {
        "sam": {
            "path": os.path.join(input_folder, "uncleaned_outputs", "company_info", "sam_uncleaned.csv"),
            "clean_func": lambda df: clean_sam(ueis, df)
        },
        "usas": {
            "path": os.path.join(input_folder, "uncleaned_outputs", "company_info", "usas_uncleaned.csv"),
            "clean_func": clean_usas
        },
        "sbir": {
            "path": os.path.join(input_folder, "uncleaned_outputs", "company_info", "sbir_uncleaned.csv"),
            "clean_func": clean_sbir
        },
        "pb": {
            "path": os.path.join(input_folder, "uncleaned_outputs", "company_info", "pb_uncleaned.csv"),
            "clean_func": lambda df: clean_pitchbook(df, pd.read_csv(f"{input_folder}/inputs/{root_tag}_pbmatches.csv"))
        }
    }

    for key, source in sources.items():
        print(f"Processing {key.upper()} data...")
        
        df = pd.read_csv(source["path"])
        cleaned_df = source["clean_func"](df)
        output_path = os.path.join(cleaned_output_dir, f"{key}_cleaned.csv")
        save_to_csv(cleaned_df, output_path)

def parse_args():
    parser = ArgumentParser(description="Fetch award and company data for a list of UEIs.")
    parser.add_argument("--input_folder", "-i", help="Path to the input folder containing the CSV files.")
    parser.add_argument("--root_tag", "-r", help="Root tag name for the csv files.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args.input_folder, args.root_tag)
