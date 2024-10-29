from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import os
import sys
from argparse import ArgumentParser
from webdriver_manager.chrome import ChromeDriverManager

# Define keywords for filtering
people_keywords = ["CEO", "COO", "CIO", "CDO", "CTO", "CFO", "CMO", "CSO", "Founder", "Co-founder"]
company_keywords = ["LLC", "INC", "Corp"]

def login(driver, username, password):
    """
    Logs into LinkedIn using the provided username and password.
    """
    driver.get('https://www.linkedin.com/login')
    time.sleep(random.uniform(5, 10))  # Random delay

    # Locate and fill in the email and password fields
    email_input = driver.find_element(By.ID, 'username')
    password_input = driver.find_element(By.ID, 'password')
    email_input.send_keys(username)
    password_input.send_keys(password)
    
    # Click the login button
    login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    login_button.click()
    
    time.sleep(random.uniform(5, 10))  # Wait for login to complete

def scrape_linkedin(driver, url):
    """
    Scrapes LinkedIn page content from the given URL using CCS_Selector.
    """
    #For both the experience and the education section if statements, they may not be necesary with the current pull to "section:has(#experience)>div>ul>li"
    if 'details/experience/' in url:
        pass
    else:
        url +='details/experience/'
   
    driver.get(url)
    data = {}
    time.sleep(random.uniform(5, 10))  # Random delay

 

    #Will need to check "job" for keywords
    experience_section = {key:[] for key in ['job','company','date','location','description']}
    jobs = driver.find_elements(By.CSS_SELECTOR, 'section:has(#experience)>div>ul>li')
    for job in jobs:
        experience_section['job']     += [job.find_element(By.CSS_SELECTOR, 'span[class="mr1 t-bold"] span').text]
        experience_section['company'] += [job.find_element(By.CSS_SELECTOR, 'span[class="t-14 t-normal"] span').text]
        experience_section['date']    += [job.find_element(By.CSS_SELECTOR, 'span[class="t-14 t-normal t-black--light"] span').text]
        experience_section['location']    += [driver.execute_script('return arguments[0].querySelector("span[class=\'t-14 t-normal t-black--light\']:nth-child(4) span")?.innerText', job)]
        experience_section['description'] += [driver.execute_script('return arguments[0].querySelector("ul li ul span[aria-hidden=true]")?.innerText', job)]
        
    data[url] = experience_section
   
    #Returns the URL to the original so it can be used for the education section
    url = url.removesuffix('details/experience/')
    return data

def scrape_education_linkedin(driver,url):
    """
    Scrapes Linkedin's edcuation details from the given URL
    """
    #For both the experience and the education section if statements, they may not be necesary with the current pull to "section:has(#experience)>div>ul>li"
    if 'details/education/' in url:
        pass
    else:
        url +='details/education/'

    driver.get(url)
    info_education = {}
    time.sleep(random.uniform(5, 10))  # Random delay

    education_section = {key:[] for key in ['school','degree','date','description']}
    colleges = driver.find_elements(By.CSS_SELECTOR, 'section:has(#education)>div>ul>li')
    for college in colleges:
        education_section['school'] += [college.find_element(By.CSS_SELECTOR, 'span[class="mr1 t-bold"] span').text]
        education_section['degree'] += [college.find_element(By.CSS_SELECTOR, 'span[class="t-14 t-normal"] span').text]
        education_section['date']   += [college.find_element(By.CSS_SELECTOR, 'span[class="t-14 t-normal t-black--light"] span').text]
        education_section['description'] += [driver.execute_script('return arguments[0].querySelector("ul li ul span[aria-hidden=true]")?.innerText', college)]

    info_education[url] = education_section
    
    #Returns the URL to the original
    url = url.removesuffix('details/education/')
    return info_education

def save_to_csv(results, batch_number):
    """
    Saves the scraping results of a batch to a CSV file.
    """
    df = pd.DataFrame(results)
    df.to_csv(f'batch_{batch_number}.csv', index=False)

def merge_csv(num_batches):
    """
    Merges all batch CSV files into one final CSV file and removes individual batch files.
    """
    all_files = [f'batch_{i}.csv' for i in range(num_batches)]
    combined_df = pd.concat([pd.read_csv(f) for f in all_files])
    combined_df.to_csv('merged_results.csv', index=False)
    
    # Optionally, remove individual batch files
    for file in all_files:
        os.remove(file)

def main(username, password):
    """
    Main function to execute the scraping workflow.
    """
    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')  # Debugging port; remove if not needed
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    login(driver, username, password)

    # Read LinkedIn links from a CSV file
    links_df = pd.read_csv('links.csv')
    urls = links_df['url'].tolist()

    batch_size = 5
    start_batch = 0
    num_batches = (len(urls) + batch_size - 1) // batch_size  

    for i in range(start_batch, num_batches):
        batch_urls = urls[i * batch_size:(i + 1) * batch_size]
        results = []

        for url in batch_urls:
            data = scrape_linkedin(driver, url)
            results.append(data)
        
        save_to_csv(results, i)
    
    merge_csv(num_batches)
    driver.quit()

def parse_args(arglist):
    """
    Parses command-line arguments for LinkedIn username and password.
    """
    parser = ArgumentParser()
    parser.add_argument("--username", "-u", required=True, help="LinkedIn username")
    parser.add_argument("--password", "-p", required=True, help="LinkedIn password")

    return parser.parse_args(arglist)

if __name__ == "__main__":
    # Parse arguments and start the main function
    args = parse_args(sys.argv[1:])
    main(args.username, args.password)
