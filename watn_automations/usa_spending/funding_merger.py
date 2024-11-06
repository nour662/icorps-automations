import os
import pandas as pd
import zipfile

folder_path = (r'C:\Users\sluca\Downloads\USA_Spending')

os.chdir(folder_path)

assistance_prime_award =  pd.DataFrame()
assistance_sub_award =  pd.DataFrame()
contract_prime_award =  pd.DataFrame()
contract_sub_award =  pd.DataFrame()

#Sorts through the saved .zip files from the USA spending website
for zip_file in os.listdir(folder_path):
    if zip_file.endswith('.zip'):
        zip_path = os.path.join(folder_path, zip_file)

        with zipfile.ZipFile(zip_path, 'r') as z:
            # Gets the list of files in the ZIP and sort them
            csv_files = [file for file in z.namelist() if file.endswith('.csv')]
            csv_files.sort() 

            if len(csv_files) > 0:
                with z.open(csv_files[0]) as f:
                    df_first = pd.read_csv(f)
                    assistance_prime_award = pd.concat([assistance_prime_award, df_first], ignore_index=True)

            # Merge the second CSV file
            if len(csv_files) > 1:
                with z.open(csv_files[1]) as f:
                    df_second = pd.read_csv(f)
                    assistance_sub_award = pd.concat([assistance_sub_award, df_second], ignore_index=True)
            
            # Merge the third CSV file
            if len(csv_files) > 2:
                with z.open(csv_files[2]) as f:
                    df_third = pd.read_csv(f)
                    contract_prime_award = pd.concat([contract_prime_award, df_third], ignore_index=True)
            
            # Merge the fourth CSV file
            if len(csv_files) > 3:
                with z.open(csv_files[3]) as f:
                    df_fourth = pd.read_csv(f)
                    contract_sub_award = pd.concat([contract_sub_award, df_fourth], ignore_index=True)

# Save the merged DataFrames to separate CSV files
assistance_prime_award.to_csv('assistance_prime_award.csv', index=False)
assistance_sub_award.to_csv('assistance_sub_award.csv', index=False)
contract_prime_award.to_csv('contract_prime_award.csv', index=False)
contract_sub_award.to_csv('contract_sub_award.csv', index=False)
        