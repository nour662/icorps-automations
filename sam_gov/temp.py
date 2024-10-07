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
        #response = requests.get(url)
        #tree = html.fromstring(response.content)

        driver.get(url)

        sleep(5)

        legal_name_xpath = driver.find_element(By.XPATH,'//h1[@class="grid-col margin-top-3 display-none tablet:display-block wrap"]/text()')
        num_uei_xpath = driver.find_element(By.XPATH,'(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"]/text())[1]')
        cage_xpath = driver.find_element(By.XPATH,'(//span[@class="wrap font-sans-md tablet:font-sans-lg h2"]/text())[2]')
        physical_address_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//li/text()')
        mailing_address_xpath = driver.find_element(By.XPATH,'//ul[contains(text(), "Mailing Address")]/following-sibling::span')
        entity_url_xpath = driver.find_element(By.XPATH,'//a[@class="usa-link"]/@href')
        start_date_xpath = driver.find_element(By.XPATH,'//span[contains(text(), "Entity Start Date")]/following-sibling::span')
        contact1_xpath = driver.find_element(By.XPATH,'//div[@class="sds-card__body padding-2"]//child::h3')
        print(legal_name_xpath)
        print(num_uei_xpath)
        if len(tree.xpath(physical_address_xpath)) == 3:
            street_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[1]')
            town_state_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[2]')
            zipcode_country_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[3]')
            suite = None
        else:
            street_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[1]')
            suite_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[2]')
            town_state_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[3]')
            zipcode_country_xpath = driver.find_element(By.XPATH,'//ul[@class="sds-list sds-list--unstyled margin-top-1"]//child::li[4]')
            suite = tree.xpath(suite_xpath)[0] if tree.xpath(suite_xpath) else None
        
        return {
            "keyword": driver.find_element(By.XPATH,keyword),
            "legal_name": driver.find_element(By.XPATH,legal_name_xpath)[0] if driver.find_element(By.XPATH,legal_name_xpath) else None,
            "num_uei": driver.find_element(By.XPATH,num_uei_xpath)[0] if driver.find_element(By.XPATH,num_uei_xpath) else None,
            "cage": driver.find_element(By.XPATH,cage_xpath)[0] if driver.find_element(By.XPATH,cage_xpath) else None,
            "street": driver.find_element(By.XPATH,street_xpath)[0] if driver.find_element(By.XPATH,street_xpath) else None,
            "suite": driver.find_element(By.XPATH,suite),
            "town_state": driver.find_element(By.XPATH,town_state_xpath)[0] if driver.find_element(By.XPATH,town_state_xpath) else None,
            "zipcode_country": driver.find_element(By.XPATH,zipcode_country_xpath)[0] if driver.find_element(By.XPATH,zipcode_country_xpath) else None,
            "mailing_address": driver.find_element(By.XPATH,mailing_address_xpath)[0] if driver.find_element(By.XPATH,mailing_address_xpath) else None,
            "entity_url": driver.find_element(By.XPATH,entity_url_xpath)[0] if driver.find_element(By.XPATH,entity_url_xpath) else None,
            "start_date": driver.find_element(By.XPATH,start_date_xpath)[0] if driver.find_element(By.XPATH,start_date_xpath) else None,
            "contact1": driver.find_element(By.XPATH,contact1_xpath)[0] if driver.find_element(By.XPATH,contact1_xpath) else None
        }
        """
        return {
            "keyword": keyword,
            "legal_name": tree.xpath(legal_name_xpath)[0] if tree.xpath(legal_name_xpath) else None,
            "num_uei": tree.xpath(num_uei_xpath)[0] if tree.xpath(num_uei_xpath) else None,
            "cage": tree.xpath(cage_xpath)[0] if tree.xpath(cage_xpath) else None,
            "street": tree.xpath(street_xpath)[0] if tree.xpath(street_xpath) else None,
            "suite": suite,
            "town_state": tree.xpath(town_state_xpath)[0] if tree.xpath(town_state_xpath) else None,
            "zipcode_country": tree.xpath(zipcode_country_xpath)[0] if tree.xpath(zipcode_country_xpath) else None,
            "mailing_address": tree.xpath(mailing_address_xpath)[0] if tree.xpath(mailing_address_xpath) else None,
            "entity_url": tree.xpath(entity_url_xpath)[0] if tree.xpath(entity_url_xpath) else None,
            "start_date": tree.xpath(start_date_xpath)[0] if tree.xpath(start_date_xpath) else None,
            "contact1": tree.xpath(contact1_xpath)[0] if tree.xpath(contact1_xpath) else None
        }"""
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def main():
    links = {}  

    chrome_options = Options()
    chrome_options.add_argument('--remote-debugging-port=9222')  
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    driver.get("https://sam.gov/content/home")

    sleep(60)  

    search_page_button = driver.find_element(By.XPATH, '//a[@id="search"]')
    search_page_button.click() 

    input_df = pd.read_csv("input.csv")
    input_list = input_df["Company_Name"].tolist()

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
