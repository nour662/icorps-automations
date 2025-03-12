import glob
import pandas as pd

# Identifies the path to the location where all the batches are placed
all_files = glob.glob(r'company_output/*.csv')
df_list = []

# Process each file
for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        # Check if the file is empty (no columns or rows)
        if temp_df.empty or temp_df.columns.size == 0:
            print(f"Skipping empty or invalid file: {file}")
            continue
        df_list.append(temp_df)
    except pd.errors.EmptyDataError:
        print(f"Skipping empty file: {file}")
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Merge and save only if valid DataFrames exist
if df_list:
    merged_df = pd.concat(df_list, ignore_index=True)
    output_path = 'company_output/merged-batches-11162024.csv'
    merged_df.to_csv(output_path, index=False)
    print(f"Merged file saved to {output_path}")
else:
    print("No valid files to merge. Please check the input directory.")
