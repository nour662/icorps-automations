import pandas as pd

file1 = pd.read_csv("../watn_automations/inputs/participant_master.csv")  
file2 = pd.read_csv("../watn_automations/inputs/company_master.csv")

file1['Company'] = file1['Company'].str.strip()
file2['Account Name'] = file2['Account Name'].str.strip()

merged_data = pd.merge(
    file1,
    file2,
    left_on='Company',       
    right_on='Account Name', 
    how='inner'             
)

merged_data = merged_data.drop(columns=['Account Name'])
merged_data = merged_data.loc[:, ~merged_data.columns.duplicated()]

merged_data.to_csv("inputs/icorps_masterlist.csv", index=False)
