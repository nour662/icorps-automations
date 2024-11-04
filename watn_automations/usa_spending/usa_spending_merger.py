import os
import pandas as pd

folder_path = (r'C:\Users\sluca\Downloads\USA_Spending')

os.chdir(folder_path)

assistance_prime_award = []
assistance_sub_award = []
contract_prime_award = []
contract_sub_award = []

for root, dirs, files in os.walk(folder_path):
    for dir in dirs:
        
        subfolder_path = os.path.join(root, dir)
        
        os.chdir(subfolder_path)

        subfolder_files = os.listdir()
        subfolder_files.sort() 
       
        if len(subfolder_files) >= 1 and subfolder_files[0].endswith('.csv'):
            df1 = pd.read_csv(subfolder_files[0])
            assistance_prime_award.append(df1)
        if len(subfolder_files) >= 2 and subfolder_files[1].endswith('.csv'):
            df2 = pd.read_csv(subfolder_files[1])
            assistance_sub_award.append(df2)
        if len(subfolder_files) >= 3 and subfolder_files[2].endswith('.csv'):
            df3 = pd.read_csv(subfolder_files[2])
            contract_prime_award.append(df3)
        if len(subfolder_files) >= 4 and subfolder_files[3].endswith('.csv'):
            df4 = pd.read_csv(subfolder_files[3])
            contract_sub_award.append(df4)

# Change back to the original folder path
os.chdir(folder_path)

# Concatenate and save each list of DataFrames to their respective CSV files
if assistance_prime_award:
    pd.concat(assistance_prime_award, ignore_index=True).to_csv('assistance_prime_award.csv', index=False)
if assistance_sub_award:
    pd.concat(assistance_sub_award, ignore_index=True).to_csv('assistance_sub_award.csv', index=False)
if contract_prime_award:
    pd.concat(contract_prime_award, ignore_index=True).to_csv('contract_prime_award.csv', index=False)
if contract_sub_award:
    pd.concat(contract_sub_award, ignore_index=True).to_csv('contract_sub_award.csv', index=False)

print("CSV files have been successfully merged into")