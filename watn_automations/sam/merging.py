import pandas as pd
import glob

"""
This script combines all of the uncleaned batches that are outputted by the "sam_gov_selenium.py" program. It merges all the 
batches into a large .csv file that displays results in the following order:

keyword,legal_name,num_uei,cage,physical_address,mailing_address,entity_url,start_date,contact1,contact2,
state_country_incorporation,congressional_district

Inaccurate records in the outputted file need to be removed in order for the data to display the targeted companies information.
The output file's name can be changed in the final line of the code by altering "sam_uncleaned_batches-10302024.csv" to the 
desired name. 
"""

#Identifies the path to the location where all the batches are placed
all_files = glob.glob(r'C:\Users\sluca\Downloads\icorps-data\watn_automations\sam\output\output-10282024\batch_*.csv')
df_list = []

#Is used to merge all batches rather than a specific range of batches
df_list = []

for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

#Outputs the data into a .csv file named "sam_uncleaned_batches-10302024.csv"
merged_df = pd.concat(df_list, ignore_index= True)
merged_df.to_csv('sam_uncleaned_batches-10302024.csv', index=False)

