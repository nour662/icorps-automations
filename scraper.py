from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import re as re
import time
import pandas as pd
import chromedriver_binary
import json
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# https://medium.com/mlearning-ai/how-to-build-a-web-scraper-for-linkedin-6b49b6b6adfc

#Input webdriver path, LinkedIn username, LinkedIn password
PATH = "C:/Users/hairb/OneDrive/Desktop/chrome-win64/chrome-win64"
# USERNAME = input("Enter the username: ")
# PASSWORD = input("Enter the password: ")
USERNAME = "your username"
PASSWORD = "your password"
print(PATH)
print(USERNAME)
print(PASSWORD)

driver = webdriver.Chrome()

# Goes to Linked In home page
time.sleep(2)
driver.get("https://www.linkedin.com/uas/login")
time.sleep(1.5)

# Logs in with the inputed criteria

email = driver.find_element(By.ID, "username")
email.send_keys(USERNAME)
password = driver.find_element(By.ID, "password")
password.send_keys(PASSWORD)
time.sleep(0.1)
password.send_keys(Keys.RETURN)
time.sleep(0.5)

# Open the JSON file
with open('links.json', 'r') as file:
    # Load JSON data from file
    data = json.load(file)

print(data)

time.sleep(2)

# Loops through links and visits each page
# Checks for intern tag in role

def remove_job_descriptor(str):
    for i in range(0, len(str)):
        if (str[i] == "·"):
            return str[0:(i-1)]
    return str

def find_largest_arr(exp_map):
    max = -1
    for exp in exp_map:
        if (len(exp_map[exp]) > max):
            max = len(exp_map[exp])
    return max

def balance_arrays(exp_map):
    max = find_largest_arr(exp_map)
    print(f"max: {max}")
    for exp in exp_map:
        while (len(exp_map[exp]) < max):
            exp_map[exp].append("")
    return exp_map
            


exp_map = {}
intern_map = {}

for i in range(0, len(data)):
    driver.get(data[i])
    time.sleep(1.5)

    jobs = driver.find_elements(By.CSS_SELECTOR, 'section:has(#experience)>div>ul>li')
    name = driver.find_element(By.TAG_NAME, "h1").text


    exp = []



    count = 0
    for job in jobs:
        try:
            child = job.find_element(By.TAG_NAME, "span")
            other_children = job.find_elements(By.TAG_NAME, "span")
            multi_role = job.find_elements(By.TAG_NAME, "a")

            print(len(other_children))

            if(len(other_children) < 17):
                company = other_children[2].find_element(By.TAG_NAME, "span").text
                company = remove_job_descriptor(company)
                exp.append(f"{company}\n({child.text})")
                print(exp[count])
                # print(child.text)
                # print(other_children[2].find_element(By.TAG_NAME, "span").text)
            else:
                # for label in multi_role:
                #     print(label.text)
                role = multi_role[2].find_element(By.TAG_NAME, "span").text
                exp.append(f"{remove_job_descriptor(child.text)}\n({role})")
                print(exp[count])
                # print(multi_role[2].find_element(By.TAG_NAME, "span").text)
                # print(child.text)
            count+=1
        except Exception:
            # This block executes if a ValueError is raised
            company = other_children[2].find_element(By.TAG_NAME, "span").text
            company = remove_job_descriptor(company)
            exp.append(f"{company}\n({child.text})")
            print(exp[count])
    
    exp_map[name] = exp

    print("*************")
    time.sleep(0.5)

print(exp_map)
exp_map = balance_arrays(exp_map)
print(exp_map)

names = []
for exp in exp_map:
    names.append(exp)

df = pd.DataFrame(data=exp_map).transpose()
df.insert(loc=0, column='Person', value=names)

print(df)

df.to_csv('experience_list.csv', index=False)  
        
driver.quit()