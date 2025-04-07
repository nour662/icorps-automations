import os
import json
import pandas as pd

def extract_json_files(root_folder):
    """Recursively fetch all JSON file paths from the directory."""
    json_files = []
    for folder_path, _, files in os.walk(root_folder):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(folder_path, file))
    return json_files

def flatten_json(record):
    """Flatten a JSON record for CSV storage up to 'pi_end_date'."""
    flat_data = {
        "awd_id": record.get("awd_id"),
        "agcy_id": record.get("agcy_id"),
        "tran_type": record.get("tran_type"),
        "awd_istr_txt": record.get("awd_istr_txt"),
        "awd_titl_txt": record.get("awd_titl_txt"),
        "cfda_num": record.get("cfda_num"),
        "org_code": record.get("org_code"),
        "po_phone": record.get("po_phone"),
        "po_email": record.get("po_email"),
        "po_sign_block_name": record.get("po_sign_block_name"),
        "awd_eff_date": record.get("awd_eff_date"),
        "awd_exp_date": record.get("awd_exp_date"),
        "tot_intn_awd_amt": record.get("tot_intn_awd_amt"),
        "awd_amount": record.get("awd_amount"),
        "awd_min_amd_letter_date": record.get("awd_min_amd_letter_date"),
        "awd_max_amd_letter_date": record.get("awd_max_amd_letter_date"),
        "awd_abstract_narration": record.get("awd_abstract_narration"),
        "awd_arra_amount": record.get("awd_arra_amount"),
        "dir_abbr": record.get("dir_abbr"),
        "org_dir_long_name": record.get("org_dir_long_name"),
        "div_abbr": record.get("div_abbr"),
        "org_div_long_name": record.get("org_div_long_name"),
        "awd_agcy_code": record.get("awd_agcy_code"),
        "fund_agcy_code": record.get("fund_agcy_code"),
    }
    
    # Extracting first PI details (assuming multiple PIs can exist)
    pi_info = record.get("pi", [{}])[0]  # Get first PI or empty dict
    flat_data.update({
        "pi_role": pi_info.get("pi_role"),
        "pi_first_name": pi_info.get("pi_first_name"),
        "pi_last_name": pi_info.get("pi_last_name"),
        "pi_mid_init": pi_info.get("pi_mid_init"),
        "pi_sufx_name": pi_info.get("pi_sufx_name"),
        "pi_full_name": pi_info.get("pi_full_name"),
        "pi_email_addr": pi_info.get("pi_email_addr"),
        "nsf_id": pi_info.get("nsf_id"),
        "pi_start_date": pi_info.get("pi_start_date"),
        "pi_end_date": pi_info.get("pi_end_date"),
    })

    return flat_data

def load_json_data(json_files):
    """Load JSON data from multiple files and flatten them."""
    data_list = []
    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for record in data:
                        data_list.append(flatten_json(record))
                else:
                    data_list.append(flatten_json(data))
        except Exception as e:
            print(f"Error loading {file}: {e}")
    return data_list

def save_to_csv(data_list, output_file):
    """Save list of dictionaries to a CSV file."""
    if not data_list:
        print("No data found to save.")
        return
    
    df = pd.DataFrame(data_list)
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"CSV file saved: {output_file}")

# Define paths
root_folder = "nsf_data"  # Change to your directory
output_csv = "output.csv"

# Process files
#json_files = extract_json_files(root_folder)
#data_list = load_json_data(json_files)
#save_to_csv(data_list, output_csv)



df= pd.read_csv('output.csv')

pi_names =pd.read_csv('test.csv')

# Extract first and last names
pi_names['pi_first_name'] = pi_names['PI'].str.split().str[0]
pi_names['pi_last_name'] = pi_names['PI'].str.split().str[-1]

# Create full name column
pi_names['pi_full_name'] = pi_names['pi_first_name'] + " " + pi_names['pi_last_name']

# Filter pi_names where "Type" == "HCT"
filtered_pi_names = pi_names[pi_names['Type'] == 'HCT']

# Create full name column in df
df['pi_full_name'] = df['pi_first_name'] + " " + df['pi_last_name']

# Match full names
matched_df = df[df['pi_full_name'].isin(filtered_pi_names['pi_full_name'])]

# Count occurrences of full names
name_counts = matched_df['pi_full_name'].value_counts().reset_index()
name_counts.columns = ['pi_full_name', 'count']

# Merge count back into pi_names
pi_names = pi_names.merge(name_counts, on='pi_full_name', how='left').fillna(0)

# Save the updated pi_names with counts
pi_names.to_csv("pi_names_with_counts.csv", index=False)

print(pi_names)

print(name_counts[name_counts['count'] > 0]['count'].sum())
print(name_counts['count'].sum())
