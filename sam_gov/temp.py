import requests 
import pandas as pd 
import csv 
from time import sleep


## Go back and delete whatever we dont need
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException




def search_keyword(keyword):
 
    pass 


def get_links(): 
    pass 



def scrape_links(): 
    pass 



def main():

    links = {}  ## define an empty dictionary to hold the multiple search results. 

    ## Definding web driver
    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')  # Debugging port; remove if not needed
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    input_df = pd.read_csv("name_list.csv")
    input_list =  input_df["Company_Name"].tolist() 

    

    for name in input_list: 
        search_input = name.lower().strip() 

        search_input = search_input.replace("." , "").replace("," , "").replace("inc" , "").replace("llc" , "").replace("corp " , "").replace("ltd" , "").replace("limited" , "").replace("pty" , "")
        
        search_keyword(search_input) 

        result_links = get_links() 

        links[name] = result_links






    pass 


if __name__  == "__main__" : 
    main() 