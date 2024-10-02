import requests 
import pandas as pd 
import csv 
from time import sleep


## Go back and delete whatever we dont need
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException , InvalidSelectorException




def search_keyword(driver, keyword):   

    search_bar = driver.find_element(By.XPATH , '//input[@name = "search"]' )
    submit_button = driver.find_element(By.XPATH , '//button[@class="usa-button ng-star-inserted"]')

    search_bar.send_keys(keyword)
    submit_button.click() 

    sleep(10)
    links  = driver.find_elements(By.XPATH , '//div[@class="grid-row grid-gap"]//a')

    return [a.get_attribute('href') for a in links]


def scrape_links(): 
    pass 


def main():

    links = {}  ## define an empty dictionary to hold the multiple search results. 

    ## Definding web driver
    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')  # Debugging port; remove if not needed
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    

    driver.get("https://sam.gov/content/home")

    sleep(60)

    search_page_button = driver.find_element(By.XPATH, '//a[@id="search"]')
    search_page_button.click() 

    input_df = pd.read_csv("name_list.csv")
    input_list =  input_df["Company_Name"].tolist() 



    domain_button = driver.find_element(By.XPATH , '//div[@class="sds-card sds-card--collapsible sds-card--collapsed ng-star-inserted"]')
    domain_button.click()


    entity_domain = driver.find_element(By.XPATH , '(//li[@class="usa-sidenav__item ng-star-inserted"])[3]')
    entity_domain.click()


    for name in input_list: 
        search_input = name.lower().strip() 

        search_input = search_input.replace("." , "").replace("," , "").replace("inc" , "").replace("llc" , "").replace("corp " , "").replace("ltd" , "").replace("limited" , "").replace("pty" , "")
        
        result_links = search_keyword(driver, search_input) 

        links[name] = result_links






    pass 


if __name__  == "__main__" : 
    main() 