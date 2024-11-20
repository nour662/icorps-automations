import pandas as pd
import glob
"""
This script combines all of the uncleaned award information batches that are outputted by the "sbir_sttr_name_search. py" program. 
It merges all the batches into a large .csv file that displays results in the following order:

Keyword Search,Company Name,Start Date,End Date,Funding Amount,Phase,Program,Solicitation Number,Source Link

The location of the output batches need to be identified on line 22 for merging.

Since companies were searched for by name, inaccurate records in the outputted file need to be removed in order for the 
data to display the targeted companies' information. Output would be much more accurate if the UEI was utilized as the search 
term instead of company name.

The output file's name can be changed in the final line of the code by altering "SBIR_award_uncleaned_batches.csv" to the 
desired name. 

**Scott Lucarelli**
"""

#Identifies the path to the location where all the batches are placed
all_files = glob.glob(r'C:\Users\sluca\Downloads\icorps-data\SBIR\award_output\award_batch_*.csv')

df_list = []

#Is used to merge all batches, rather than a specific range of batches

df_list = []

for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

#Output the master merged folder as the following .csv file name
merged_df = pd.concat(df_list, ignore_index= True)
merged_df.to_csv('SBIR_award_uncleaned_batches.csv', index=False)