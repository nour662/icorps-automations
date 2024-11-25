import pandas as pd 

def clean_masterlist(df, output_file): 
    df["Full Name"] = df["First Name"] + " " + df["Last Name"]
    
    df = df.drop(columns=["First Name", "Last Name"])

    grouped = (
        df.groupby('Company')[[
            "Full Name", 
            "Shipping Street", 
            "Shipping City", 
            "Shipping State/Province", 
            "Shipping Country"]]
        .agg(lambda x: list(x))  
        .reset_index()
    )
    
    # Join the 'Full Name' column into a comma-separated list
    grouped['sf_full_names'] = grouped['Full Name'].apply(lambda x: ", ".join(x))
    # For all other columns, take the first value (assuming they are the same across rows per company)
    grouped['sf_street'] = grouped['Shipping Street'].apply(lambda x: x[0])
    grouped['sf_city'] = grouped['Shipping City'].apply(lambda x: x[0])
    grouped['sf_state'] = grouped['Shipping State/Province'].apply(lambda x: x[0])
    grouped['sf_country'] = grouped['Shipping Country'].apply(lambda x: x[0])


    grouped = grouped.drop(columns=[ "Full Name", "Shipping Street", "Shipping City" , "Shipping State/Province", "Shipping Country" ])
    print(grouped)

    grouped.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

    return grouped


def main(): 
    input_file = "../inputs/icorps_masterlist.csv"
    output_file = "cleaned_masterlist.csv"

    master_list = pd.read_csv(input_file)
    clean_masterlist(master_list, output_file)
    

if __name__ == "__main__": 
    main()
