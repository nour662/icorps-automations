import pandas as pd
import glob

all_files = glob.glob(r'C:\Users\sluca\Downloads\icorps-data\sam_gov\output\batch_*.csv')

df_list = []

for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

merged_df = pd.concat(df_list, ignore_index= True)
merged_df.to_csv('merged_batches(1-23).csv', index=False)