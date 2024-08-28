from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import re as re
import time
import pandas as pd
from argparse import ArgumentParser
import chromedriver_binary
import json
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import sys

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

##login 
## load json 
## split into different batches 
## go to each url in each batch

#######First priority: 
## scrape all expierence information 
## Save it to csv "whatever-batch-x.csv"
## continue looping until finished
## merge all csv. 





######## Second priority.... (doesnt need to be done rn)
## get the university based on the time of enrollment in i-corps (before or during but not after)
## Scrape that university, and their stanidng






## clean exp merged csv by search for keyword/or other
### check whether or not they match the team name on file















# https://medium.com/mlearning-ai/how-to-build-a-web-scraper-for-linkedin-6b49b6b6adfc


people_keywords = ["CEO" , "COO" , "CIO" , "CDO" , "CTO" , "CFO", "CMO" , "CSO", "Founder" , "Co-founder"]
company_keywords = ["LLC" , "INC", "Corp"]



def login(username, passoword) : 
    ### DONE, needs comments
    email = driver.find_element(By.ID, "username")
    email.send_keys(username)
    password = driver.find_element(By.ID, "password")
    password.send_keys(passoword)
    time.sleep(0.1)
    password.send_keys(Keys.RETURN)
    time.sleep(0.5)
            

def scr(url): 



"""for i in range(0, len(data)):
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
    time.sleep(0.5)"""



def main(username, password ):


    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--remote-debugging-port=9222')  # Use the same port as used to start Chrome

    driver = webdriver.Chrome(options=chrome_options)

    # Goes to Linked In home page
    #time.sleep(2)
    #driver.get("https://www.linkedin.com/uas/login")
    #time.sleep(1.5)


    #login(username, password)

    with open('links.json', 'r') as file:
        data = json.load(file)

    batch_size = 1 
    start_batch = 0
    for i in range(start_batch, len(data) , batch_size):

        results = scrape_linkedin()
        save_to_csv()


    merge_csv()

    driver.quit


def parse_args(arglist):
    ## DONE: needs comments

    parser = ArgumentParser()
    parser.add_argument( "--username" , "-u", help="linkedin username")
    parser.add_argument("--password" , "-p", nargs="*", help="linkedin password")

    return parser.parse_args(arglist)

if __name__ == "__main__":
    #DONE, needs commetns
    args = parse_args(sys.argv[1:])
    main(args.username, args.password)