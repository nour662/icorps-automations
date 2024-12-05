import pandas as pd 

def clean_masterlist(df): 
    df["Full Name"] = df["First Name"] + " " + df["Last Name"]
    
    df = df.drop(columns=["First Name", "Last Name"])

    grouped = (
        df.groupby('Company')[[
            "Full Name", 
            "Shipping Street", 
            "Shipping City", 
            "Shipping State/Province", 
            "Shipping Country", 
            "Website"]]
        .agg(lambda x: list(x))  
        .reset_index()
    )
    
    grouped['sf_company_name'] = grouped['Company'].lower()
    grouped['sf_contacts'] =grouped['Full Name'].apply(lambda x : x.lower())
    grouped['sf_street'] = grouped['Shipping Street'].apply(lambda x: x[0])
    grouped['sf_city'] = grouped['Shipping City'].apply(lambda x: x[0])
    grouped['sf_state'] = grouped['Shipping State/Province'].apply(lambda x: x[0])
    grouped['sf_country'] = grouped['Shipping Country'].apply(lambda x: x[0])
    grouped['sf_website'] = grouped['Website'].apply(lambda x: x[0])

    grouped = grouped.drop(columns=[ "Company", "Full Name", "Shipping Street", "Shipping City" , "Shipping State/Province", "Shipping Country" , "Website" ])
    
    return grouped

def clean_training(df): 

   df["sam_company_name"] =  df["legal_name"].lower()
    



def fuzzy_match(master_list, ): 
    pass


def train_model(supervised): 


    pass 


def main(): 
    input_file_one = "../inputs/icorps_masterlist.csv"
    input_file_two = "../outputs/outputs_11212024/merged_files/same_uncleaned.csv" 

    training_csv = "training.csv"


    master_df = pd.read_csv(input_file_one)
    master_df  = clean_masterlist(master_df)

    training_df = pd.read_csv(training_csv)
    clean_training(training_df)

    

if __name__ == "__main__": 
    main()
