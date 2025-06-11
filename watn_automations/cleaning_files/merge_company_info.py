import col_converts
import pandas as pd
import os
from argparse import ArgumentParser

def make_final_output(input_file, output_path, usas, sbir, sam, pb):
    cols = col_converts.get_compinfo_final_cols()

    final_output = pd.DataFrame(columns=cols).astype(str)
    input_file = pd.read_csv(input_file, dtype={"UEI": str, "DUNS": str, "Zip Code": str})

    final_output["Account Name"] = input_file["Company"].unique()
    name_to_uei = input_file.set_index("Company")["UEI"].to_dict()
    final_output["UEI"] = final_output["Account Name"].map(name_to_uei)
    
    final_output = final_output[
        final_output["UEI"].isin(sam["UEI"]) | final_output["Account Name"].isin(pb["Account Name"])
    ]

    optional_fields = {
        "DUNS": "DUNS",
        "Website": "Company Website"
    }
    for input_col, output_col in optional_fields.items():
        if input_col in input_file.columns:
            final_output[output_col] = input_file[input_col]

    def dynamic_map(source_df, key_col, fields, target_df, target_key):
        for src, tgt in fields.items():
            target_df[tgt] = target_df[target_key].map(source_df.set_index(key_col)[src])

    sam_fields = {
        "CAGE": "CAGE",
        "Incorporation State": "Incorporation State",
        "Incorporation Country": "Incorporation Country",
        "Incorporation Date": "Incorporation Date"
    }
    dynamic_map(sam, "UEI", sam_fields, final_output, "UEI")

    pb_fields = {
        "Industry": "Industry",
        "Annual Revenue Range": "Annual Revenue Range",
        "Description": "Description",
        "Status": "Active",
        "Employees": "Employees"
    }

    for src, tgt in pb_fields.items():
        mapped = final_output["Account Name"].map(pb.set_index("Account Name")[src])
        final_output[tgt] = mapped.apply(lambda x: x != "Out of Business") if src == "Status" else mapped

    sbir_states = sbir[["UEI", "Employees", "State"]].copy()
    sam_states = sam[["UEI", "State"]].copy()

    sbir_sam_merge = sbir_states.merge(sam_states, on="UEI", suffixes=("_sbir", "_sam"))

    sbir_sam_merge = sbir_sam_merge[
        sbir_sam_merge["State_sbir"].str.upper() == sbir_sam_merge["State_sam"].str.upper()
    ]

    sbir_valid_emp = sbir_sam_merge.set_index("UEI")["Employees"]
    final_output["SBIR_Employees"] = final_output["UEI"].map(sbir_valid_emp)

    final_output["Employees"] = final_output["Employees"].replace(["", " ", "nan", "None"], pd.NA)
    final_output["SBIR_Employees"] = final_output["SBIR_Employees"].replace(["", " ", "nan", "None"], pd.NA)
    final_output["Employees"] = final_output["Employees"].fillna(final_output["SBIR_Employees"])

    final_output.drop(columns=["SBIR_Employees"], inplace=True)

    final_output["DUNS"] = final_output.apply(
        lambda row: usas.set_index("UEI")["DUNS"].get(row["UEI"], row.get("DUNS")), axis=1
    )

    def fallback_get(row, primary_df, secondary_df, col):
        val = primary_df.set_index("UEI")[col].get(row["UEI"])
        if pd.notna(val):
            return val
        return secondary_df.set_index("UEI")[col].get(row["UEI"])

    final_output["Legislative District"] = final_output.apply(
        lambda row: fallback_get(row, sam, usas, "Legislative District"), axis=1
    )

    def name_get(row):
        name = sam.set_index("UEI")["Legal Name"].get(row["UEI"])
        if pd.notna(name):
            return name
        return pb.set_index("Account Name")["Legal Name"].get(row["Account Name"])

    final_output["Legal Name"] = final_output.apply(name_get, axis=1)
    final_output["Company Exists"] = final_output["Account Name"].isin(pb["Account Name"]) | final_output["UEI"].isin(sam["UEI"])

    final_output["Incorporation Type"] = final_output["Legal Name"].apply(
        lambda name: "Corporation" if "Inc" in str(name) else ("Limited Liability Company (LLC)" if "LLC" in str(name) else None)
    )

    final_output["Incorporation Year"] = final_output.apply(
        lambda row: pb.set_index("Account Name")["Incorporation Year"].get(row["Account Name"])
        if pd.notna(pb.set_index("Account Name")["Incorporation Year"].get(row["Account Name"]))
        else pd.to_datetime(row["Incorporation Date"], errors='coerce').year,
        axis=1
    )

    abbrev = col_converts.get_state_abbreviations()
    sam_addr = sam.set_index("UEI")[["Street Address", "City", "State", "Zip Code"]].astype(str)
    pb_addr = pb.set_index("Account Name")[["Street Address", "City", "State"]]

    def address_block(row):
        if row["UEI"] in sam_addr.index:
            return sam_addr.loc[row["UEI"]]
        elif row["Account Name"] in pb_addr.index:
            addr = pb_addr.loc[row["Account Name"]]
            return pd.Series({
                "Street Address": addr["Street Address"],
                "City": addr["City"],
                "State": addr["State"],
                "Zip Code": None
            })
        return pd.Series([None]*4, index=["Street Address", "City", "State", "Zip Code"])

    final_output[["Street Address", "City", "State", "Zip Code"]] = final_output.apply(address_block, axis=1).apply(pd.Series)
    final_output["Country"] = final_output["State"].apply(lambda s: "United States" if s in abbrev else None)

    def website_get(row):
        site = sam.set_index("UEI")["Company Website"].get(row["UEI"])
        if pd.notna(site):
            return site
        return pb.set_index("Account Name")["Company Website"].get(row["Account Name"], row.get("Company Website"))

    final_output["Company Website"] = final_output.apply(website_get, axis=1)
    final_output.to_csv(f"{output_path}/company_info.csv", index=False)
    return final_output

def main(input_file, data_path, output_path):

    usas = pd.read_csv(f"{data_path}/usas_cleaned.csv", dtype={"DUNS": str})
    sbir = pd.read_csv(f"{data_path}/sbir_cleaned.csv", dtype={"Employees": str, "Zip Code": str, "State":str})
    sam = pd.read_csv(f"{data_path}/sam_cleaned.csv")
    pb = pd.read_csv(f"{data_path}/pb_cleaned.csv", dtype={"Employees": str, "Incorporation Year": str})

    make_final_output(input_file, output_path, usas, sbir, sam, pb)


def parse_args(): 
    parser = ArgumentParser(description="")
    parser.add_argument("--input_file", "-i", type=str, required=True, help="Path to original ETL input file.")
    parser.add_argument("--data_path", "-d", type=str, required=True, help="Directory of cleaned data files.")
    parser.add_argument("--output_path", "-o", type=str, required=True, help="Output directory for final merged data.")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args.input_file, args.data_path, args.output_path)