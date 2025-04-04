import shutil
import pandas as pd
from bs4 import BeautifulSoup
import glob
import os

def extract_content(webarchive_file, html_path): 
    with open(webarchive_file, 'rb') as webarchive_file:
        with open(html_path, 'wb') as html_file:
            shutil.copyfileobj(webarchive_file, html_file)

def camelCase(name): 
    name = name.strip().split()
    words = [word.title() if i != 0 else word.lower() for i, word in enumerate(name)]
    return "".join(words)

def santize_cols(cols): 
    changes = {"Website": "Company Website",
               "Company Legal Name": "Legal Name",
               "Deal ID": "Deal PB ID",
               "Company ID": "Company PB ID"}
    cols = ["Company" if "Companies" in col else changes.get(col, col) for col in cols]
    cols = [camelCase(col) for col in cols]
    return cols

def get_companies_list(soup): 
    company_elem = soup.find_all('span', class_='entity-hover ellipsis entity-format__entity-profile')
    return [company.get_text() for company in company_elem]

def get_table_headers(soup): 
    col_elem = soup.find_all('div', class_='smart-caption smart-caption_038bbd88 smart-caption__static smart-caption__static_038bbd88')
    return [str(col.get_text()) for col in col_elem]

def get_table_content(soup, col_ids, companies): 
    right_table = soup.find('div', id='search-results-data-table-right')
    search_rows = right_table.find_all('div', id=lambda x: x and x.startswith("search-results-data-table-row-"), class_="data-table__row")
    
    data_list = []  
    for row in search_rows: 
        data = {col_id: None for col_id in col_ids} 
        
        for col_id in col_ids:
            cell = row.find('div', {'data-id': col_id}) 
            if cell:
                title_tag = cell.find(['span', 'p'])
                if title_tag and title_tag.get('title'):
                    data[col_id] = title_tag['title']
                elif title_tag and title_tag.text.strip():
                    data[col_id] = title_tag.text.strip()
        
        if companies: 
            company = companies.pop(0)
            data["company"] = company
        
        data_list.append(data)  
    return data_list  

def save_to_csv(data_list, filename):
    df = pd.DataFrame(data_list)
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def main(): 
    webarchive_path = os.path.join(os.getcwd(), "webarchives")
    files = glob.glob(os.path.join(webarchive_path, '*.webarchive'))
    
    for file in files:
        div = "company_info" if "company" in file else "deal_info"
        html_path = os.path.join(os.getcwd(), "extracted_info.html")
        extract_content(file, html_path)

        with open(html_path, 'rb') as html_file:
            html_content = html_file.read()
            soup = BeautifulSoup(html_content, 'html.parser')
        
        table_headers = get_table_headers(soup)
        companies = get_companies_list(soup)
        col_ids = santize_cols(table_headers)
        data = get_table_content(soup, col_ids, companies)
        
        save_to_csv(data, f"{div}.csv")
        os.remove(html_path)

if __name__ == "__main__":  
    main()
