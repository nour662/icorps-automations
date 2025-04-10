import requests
import json
import pandas as pd

url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

ueis = pd.read_csv('test.csv')['num_uei'].tolist() 

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
    ]}

all_data = []

for uei in ueis:
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

df = pd.DataFrame(all_data)

# Save the DataFrame to a CSV file
df.to_csv('spending_data.csv', index=False)
print("Data has been saved to 'spending_data.csv'.")
