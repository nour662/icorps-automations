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
    Scrapes LinkedIn page content from the given URL.
    """
    driver.get(url)
    time.sleep(random.uniform(5, 10))  # Random delay

 

    data = [] 


    #TO - DO, write this section. Look into old scraping examples.

    return data

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
