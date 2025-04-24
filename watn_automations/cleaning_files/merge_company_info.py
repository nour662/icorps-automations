import col_converts
import pandas as pd
import os

def make_final_output(original_input, usas, sbir, sam, pb):
    cols = col_converts.get_compinfo_final_cols()
    final_output = pd.DataFrame(columns=cols).astype(str)
    final_output["Account Name"] = original_input["Company"]
    final_output["UEI"] = original_input["UEI"]

    final_output = final_output[
        final_output["UEI"].isin(sam["UEI"]) | final_output["Account Name"].isin(pb["Account Name"])
    ]

    optional_fields = {
        "DUNS": "DUNS",
        "Website": "Company Website"
    }
    for input_col, output_col in optional_fields.items():
        if input_col in original_input.columns:
            final_output[output_col] = original_input[input_col]

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
    final_output.to_csv("final_output.csv", index=False)
    return final_output

def main():
    input_path = "outputs/outputs_psu_incubator_companies_2025-04-22/"
    original_input = pd.read_csv(f"{input_path}/inputs/psu_incubator_companies.csv")
    usas = pd.read_csv(f"{input_path}/cleaned_outputs/company_info/usas_cleaned.csv", dtype={"DUNS": str})
    sbir = pd.read_csv(f"{input_path}/cleaned_outputs/company_info/sbir_cleaned.csv", dtype={"Zip Code": str})
    sam = pd.read_csv(f"{input_path}/cleaned_outputs/company_info/sam_cleaned.csv")
    pb = pd.read_csv(f"{input_path}/cleaned_outputs/company_info/pb_cleaned.csv", dtype={"Employees": str, "Incorporation Year": str})
    print(os.getcwd())
    make_final_output(original_input, usas, sbir, sam, pb)

if __name__ == "__main__":
    main()