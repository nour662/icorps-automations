import pandas as pd
import glob

#Identifies the path to the location where all the batches are placed
all_files = glob.glob(r'C:\Users\sluca\Downloads\icorps-data\SBIR\company_output\company_batch_*.csv')

df_list = []

#Is used to merge all batches rather than a specific range of batches

df_list = []

for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

merged_df = pd.concat(df_list, ignore_index= True)
merged_df.to_csv('SBIR_company_name_uncleaned_batches.csv', index=False)
