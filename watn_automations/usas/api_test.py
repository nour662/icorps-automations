import requests
import json
import pandas as pd
import numpy as np



url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

ueis = pd.read_csv('test.csv')['UEI'].tolist() 

headers = {
    "Content-Type": "application/json"
}

payload_template = {
    "filters": {
        "recipient_search_text": [],  
        "award_type_codes": ["A", "B", "C", "D"]
    },
    "fields": [
        "Recipient Name", "Start Date", "End Date", "Award Amount",
        "Awarding Agency", "Awarding Sub Agency", "Contract Award Type",
        "Award Type", "Funding Agency", "Funding Sub Agency"
    ], 
    
    "limit": 100}

all_data = []

for uei in ueis:
    if not uei is np.nan : 
        payload = payload_template.copy()
        payload["filters"]["recipient_search_text"] = [uei]

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            print(data)
            awards = data.get("results", [])
            
            if awards:
                for award in awards:
                    all_data.append(award)
        else:
            print(f"Request failed for UEI {uei} with status code {response.status_code}")
    else: 
        pass 



df = pd.DataFrame(all_data)


df.to_csv('spending_data.csv', index=False)
print("Data has been saved to 'spending_data.csv'.")
