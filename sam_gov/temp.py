import requests 
import pandas as pd 
import csv 
from time import sleep
from lxml import html


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


def scrape_links(keyword, url): 
    response = requests.get(url)
    tree = html.fromstring(response.content)

    legal_name_xpath = '//h1[@class="grid-col margin-top-3 display-none tablet:display-block wrap"]/text()'
    num_uei_xpath = '(//span[@class = "wrap font-sans-md tablet:font-sans-lg h2"]/text())[1]'
    cage_xpath = '(//span[@class = "wrap font-sans-md tablet:font-sans-lg h2"]/text())[2]'
    physical_address_xpath= '//ul[@class="sds-list sds-list--unstyled margin-top-1"]//li/text()'    
    mailing_address_xpath= '//ul[contains(text(), "Mailing Address")]/following-sibling::span'
    entity_url_xpath= '//a[@class="usa-link"]/@href'
    start_date_xpath = '//span[contains(text(), "Entity Start Date")]/following-sibling::span'
    contact1_xpath = '//div[@class = "sds-card__body padding-2"]//child::h3'
    #contact1_position_xpath ='(//span[@class ="ng-star-inserted"]/text())[5]'
    #contact2_xpath= 
    #contact2_position_xpath = '(//span[@class ="ng-star-inserted"]/text())[6]'
    if len(physical_address_xpath) ==3:
        street_xpath ='//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[1]' 
        town_state_xpath = '//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[2]' 
        zipcode_country_xpath = '//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[3]'
    elif len(physical_address_xpath)== 4: 
        street_xpath ='//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[1]' 
        suite_xpath ='//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[2]'
        town_state_xpath = '//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[3]' 
        zipcode_country_xpath = '//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[4]'

    legal_name = tree.xpath(legal_name_xpath)
    num_uei= tree.xpath(num_uei_xpath)
    cage = tree.xpath(cage_xpath)
    physical_address = tree.xpath(physical_address_xpath) 
    mailing_address = tree.xpath(mailing_address_xpath) 
    entity_url= tree.xpath(entity_url_xpath)
    start_date = tree.xpath(start_date_xpath)
    contact1 = tree.xpath(contact1_xpath)
    #contact1_position = tree.xpath(contact1_position_xpath)
    contact2 = tree.xpath(contact2_xpath)
    #contact2_postion = tree.xpath(contact2_position_xpath)
    if len(physical_address_xpath) < 4:
        street =tree.xpath(street_xpath)
        town_state =tree.xpath(town_state_xpath)
        zipcode_country =tree.xpath(zipcode_country_xpath)
    else: 
        street =tree.xpath(street_xpath)
        suite = tree.xpath(suite_xpath)
        town_state =tree.xpath(town_state_xpath)
        zipcode_country =tree.xpath(zipcode_country_xpath)
    
    return None


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






     


if __name__  == "__main__" : 
    main() 