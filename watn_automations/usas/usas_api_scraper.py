import pandas as pd
from time import sleep
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import numpy as np
import csv
import requests
import json

# graveyard >:3
'''
input_file = "watn_automations\\usas\\small_uei.csv"
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    input_df = pd.read_csv(input_file)
    if 'num_uei' not in input_df.columns:
        print("The CSV must contain a 'UEI' column.")
        return

    input_list = input_df['num_uei'].tolist()

    # # Configure Chrome WebDriver options
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--remote-debugging-port=9230")
    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    # Award Data extracted for Grants -- not available for every UEI  
    payload2=  {"filters": {
        "recipient_search_text":['JD35KEUVYS94'],
        "award_type_codes": ["02", "03" , "04" , "05"]
      },
      "fields": ["Recipient Name", "Start Date",
          "End Date",
          "Award Amount",
          "Awarding Agency",
          "Awarding Sub Agency",
          "Contract Award Type",
          "Award Type",
          "Funding Agency",
          "Funding Sub Agency"],
      "limit": 100
    }

    response1 = requests.post(base_url, headers=header, json=payload1)
    response2 = requests.post(base_url, headers=header, json=payload2)
    # print(response.status_code)
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        print("data2:", data1)
        data2 = response2.json()
        print("data2:", data2)

   
    # need to read UEI's from input csv
    def uei_list (file_path):
        with open (file_path, mode = 'r') as file:
            reader = csv.DictReader(file)
            return [row["UEI"].strip() for row in reader if row["UEI"].strip()] 
            # list is going to be unfriendly, write the loop and append "carter will do this"

    #search recipient and award data
    def get_data (uei):
        response = requests.post( # find uei
            base_url,
            json = {"text":uei} #put uei into csv, with column uei
        )
        
    # response.raise_for_status
    # data = response.json()
    # if not data["results"] :
    #     return None
    # return data["results"][0]
'''
def get_company_info(recipient_ids, data_list): 
    for recipient_id in recipient_ids:
        recipient_url = f"https://api.usaspending.gov/api/v2/recipient/{recipient_id}/"

        response = requests.get(recipient_url)
        if response.status_code == 200:
            data = response.json()
            company_uei = data["uei"]
            name = data["name"]
            duns = data["duns"]
            location = data["location"]
            address_line1, address_line2, city, state, zip, congressional_code = clean_location_dict(location)
            
            company_data = {
                "uei": company_uei,
                "recipient_id":recipient_id,
                "name": name,
                "duns": duns,
                "address_line1": address_line1,
                "address_line2": address_line2,
                "city": city,
                "state": state,
                "zip": zip,
                "congressional_code": congressional_code
            }
            print(company_data)
            data_list.append(company_data)
        else:
            print(f"Ruh Roh: {response.status_code}")
            print(response.text)
    return data_list

def clean_location_dict(location):
    address_line1 = location["address_line1"]
    address_line2 = location["address_line2"]
    city = location["city_name"]
    state = location["state_code"] 
    zip = location["zip"]
    congressional_code = location["congressional_code"]
    
    return address_line1, address_line2, city, state, zip, congressional_code
    
def get_data (response, all_data):
    if response.status_code == 200:
        data = response.json()
        awards = data.get("results", [])
        # print(awards)

        if awards:
            for award in awards:
                all_data.append(award)
        return all_data
    else:
        return None
                
def main():
    # API stuff I guess :)
    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    
    uei_list = pd.read_csv("watn_automations\\usas\\small_uei.csv")["num_uei"].tolist()

    # define the input filters we want and the output data tags we want
    header = {
        "Content-Type" : "application/json"
    }
    # Award Data extracted for contracts -- not available for every UEI
    payload =  {"filters": {
        "recipient_search_text":["ZZKFKXNTMMA3"],
        "award_type_codes": ["A", "B" , "C" , "D"]
      },
      "fields": [
          "Recipient Name",
          "Recipient UEI",
          "recipient_id",
          "Start Date",
          "End Date",
          "Award Amount",
          "Awarding Agency",
          "Awarding Sub Agency",
          "Contract Award Type",
          "Award Type",
          "Funding Agency",
          "Funding Sub Agency"],
      "limit": 100
    }

    all_contract_data = []
    all_grant_data = []
    try: 
        for uei in uei_list:
            if not uei is np.nan : 
                payload = payload.copy()
                payload["filters"]["recipient_search_text"] = [uei]
                
                # get contract data in a list 
                payload["filters"]["award_type_codes"] = ["A", "B" , "C" , "D"]
                response1 = requests.post(base_url, headers=header, json=payload)
                if get_data(response1, all_contract_data) :
                    all_contract_data = get_data(response1, all_contract_data)
                else:
                    print(f"Request failed for UEI {uei} with status code {response1.status_code}")
                
                # get grant data in a list 
                payload["filters"]["award_type_codes"] = ["02", "03" , "04" , "05"]
                response2 = requests.post(base_url, headers=header, json=payload)
                if get_data(response2, all_grant_data):
                    all_data_grant = get_data(response2, all_grant_data)
                else: 
                    print(f"Request failed for UEI {uei} with status code {response2.status_code}")
                print(f'{uei} Processed')
            else: 
                pass 
    except Exception as e:
        print(f'{uei} Could not Be Processed: {e}')

    contract_df = pd.DataFrame(all_contract_data)
    grant_df = pd.DataFrame(all_grant_data)

    contract_df.to_csv('watn_automations\\usas\\spending_data_contracts.csv', index=False)
    print("Data has been saved to 'spending_data_contracts.csv'.")
    grant_df.to_csv('watn_automations\\usas\\spending_data_grants.csv', index=False)
    print("Data has been saved to 'spending_data_grants.csv'.")
    
    recipient_ids = pd.read_csv("watn_automations\\usas\\spending_data_contracts.csv")["recipient_id"].tolist()
    recipient_ids.extend(pd.read_csv("watn_automations\\usas\\spending_data_grants.csv")["recipient_id"].tolist())
    recipient_ids = list(set(recipient_ids))
    
    gen_company_data = []
    gen_company_data = get_company_info(recipient_ids, gen_company_data)
    df = pd.DataFrame(gen_company_data)
    df.to_csv('watn_automations\\usas\\usas_company_data.csv', index=False)
        
if __name__ == "__main__":
    main()
