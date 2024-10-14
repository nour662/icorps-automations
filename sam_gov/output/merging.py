import pandas as pd
import glob

all_files = glob.glob(r'C:\Users\sluca\Downloads\icorps-data\sam_gov\output\batch_*.csv')

df_list = []

for file in all_files:
    # Extract the batch number from the file name
    batch_number = int(file.split('batch_')[1].split('.csv')[0])
    
    # Check if the batch number is within the desired range
    if 46 <= batch_number <= 60:
        try:
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

if df_list:
    merged_df = pd.concat(df_list, ignore_index=True)
    merged_df.to_csv('merged_batches(46-60).csv', index= False)

"""

df_list = []

for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

merged_df = pd.concat(df_list, ignore_index= True)
merged_df.to_csv('merged_batches(23-45).csv', index=False)
"""