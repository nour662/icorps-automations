import requests
import pandas as pd
from time import sleep
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

def search_keyword(driver, keyword):
    search_bar = driver.find_element(By.XPATH, '//input[@name="search"]')
    submit_button = driver.find_element(By.XPATH, '//button[@class="usa-button ng-star-inserted"]')

    search_bar.send_keys(keyword)
    submit_button.click()

    sleep(10)  
    links = driver.find_elements(By.XPATH, '//div[@class="grid-row grid-gap"]//a')

    return [a.get_attribute('href') for a in links]

def scrape_links(driver,keyword, url): 
    try:
        driver.get(url)

        sleep(5)

        legal_name = driver.find_element(By.XPATH,'//h1[@class="grid-col margin-top-3 display-none tablet:display-block wrap"]').text
        num_uei = driver.find_element(By.XPATH,'(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[1]').text
        cage = driver.find_element(By.XPATH,'(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"])[2]').text
        physical_address = driver.find_element(By.XPATH,'//ul[@class ="sds-list sds-list--unstyled margin-top-1"]').text
        mailing_address = driver.find_element(By.XPATH,'(//ul[@class="sds-list sds-list--unstyled"])[2]').text 
        entity_url = driver.find_element(By.XPATH,'//a[@class="usa-link"]').get_attribute('href')
        start_date = driver.find_element(By.XPATH,'//span[contains(text(), "Entity Start Date")]/following-sibling::span').text
        contact1 = driver.find_element(By.XPATH,'(//div[@class="sds-card__body padding-2"]//child::h3)[1]').text
        contact_2 = driver.find_element(By.XPATH,'(//div[@class="sds-card__body padding-2"]//child::h3)[2]').text
        state_country_incorporation = driver.find_element(By.XPATH,'(//div[@class= "grid-col-6 sds-field ng-star-inserted"])[3]//span[2]').text
        congressional_district = driver.find_element(By.XPATH, '(//div[@class= "grid-col-6 sds-field"])[3]//span[2]').text
        
        physical_address_lines = physical_address.split('\n')
        result1 = ','.join(physical_address_lines)
       
        mailing_address_lines = mailing_address.split('\n')
        result2 = ','.join(mailing_address_lines)

        
        return {
            "keyword": keyword,
            "legal_name": legal_name if legal_name else None,
            "num_uei": num_uei if num_uei else None,
            "cage": cage if cage else None,
            "physical_address": result1 if physical_address else None,
            "mailing_address": result2 if mailing_address else None,
            "entity_url": entity_url if entity_url else None,
            "start_date": start_date if start_date else None,
            "contact1": contact1 if contact1 else None,
            "contact2": contact_2 if contact_2 else None,
            "state_country_incorporation": state_country_incorporation if state_country_incorporation else None,
            "congressional_district ": congressional_district if congressional_district  else None,
        }
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def main():
    links = {} 

    input_df = pd.read_csv("sam_gov/input.csv")
    input_list = input_df["Company_Name"].tolist()

    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')  
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    driver.get("https://sam.gov/content/home")

    sleep(60)  

    search_page_button = driver.find_element(By.XPATH, '//a[@id="search"]')
    search_page_button.click() 


    sleep(2)


    domain_button = driver.find_element(By.XPATH , '//div[@class="sds-card sds-card--collapsible sds-card--collapsed ng-star-inserted"]')
    domain_button.click()

    entity_domain = driver.find_element(By.XPATH , '(//li[@class="usa-sidenav__item ng-star-inserted"])[3]')
    entity_domain.click()

    for name in input_list: 
        search_input = name.lower().strip()

        search_input = search_input.replace(".", "").replace(",", "").replace("inc", "").replace("llc", "").replace("corp", "").replace("ltd", "").replace("limited", "").replace("pty", "")
        
        result_links = search_keyword(driver, search_input)
        links[name] = result_links

    links_data = [] 
    print(links)

    for keyword, urls in links.items():  
        for url in urls: 
            result = scrape_links(driver,keyword, url)
            if result:
                links_data.append(result)

    driver.quit()  

    output_df = pd.DataFrame(links_data)
    output_df.to_csv('scraped_links.csv', index=False)

if __name__ == "__main__":
    main()
