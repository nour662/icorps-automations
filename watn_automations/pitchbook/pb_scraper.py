import shutil
import pandas as pd
from bs4 import BeautifulSoup
import glob
import sys 
from argparse import ArgumentParser
import os

def extract_content(webarchive_file, html_path) -> None: 
    """
    Extracts the content of a web archive file and writes it to an HTML file.
    Arguments:
        webarchive_file (str): The path to the input web archive file.
        html_path (str): The path to the output HTML file where the content will be written.
    Returns:
        None
    """
    
    with open(webarchive_file, 'rb') as webarchive_file:
        with open(html_path, 'wb') as html_file:
            shutil.copyfileobj(webarchive_file, html_file)

def camelCase(name) -> str: 
    name = name.strip().split()
    words = [word.title() if i != 0 else word.lower() for i, word in enumerate(name)]
    return "".join(words)

def santize_cols(cols) -> list: 
    """
    Sanitizes a list of column names by applying specific transformations.

    This function performs the following operations:
    1. Replaces specific column names based on a predefined mapping.
    2. Replaces any column containing the word "Companies" with "Company".
    3. Converts all column names to camelCase format using the `camelCase` function.

    Arguments:
        cols (list of str): A list of column names to be sanitized.

    Returns:
        list of str: A list of sanitized column names.
    """
    changes = {"Website": "Company Website",
               "Company Legal Name": "Legal Name",
               "Deal ID": "Deal PB ID",
               "Company ID": "Company PB ID"}
    cols = ["Company" if "Companies" in col else changes.get(col, col) for col in cols]
    cols = [camelCase(col) for col in cols]
    return cols

def get_companies_list(soup) -> list: 
    company_elem = soup.find_all('span', class_='entity-hover ellipsis entity-format__entity-profile')
    return [company.get_text() for company in company_elem]

def get_table_headers(soup) -> list : 
    col_elem = soup.find_all('div', class_='smart-caption smart-caption_038bbd88 smart-caption__static smart-caption__static_038bbd88')
    return [str(col.get_text()) for col in col_elem]

def get_table_content(soup, col_ids, companies) -> list: 
    """
    Extracts table content from a BeautifulSoup object and returns it as a list of dictionaries.

    Argumet:
        soup (bs4.BeautifulSoup): A BeautifulSoup object representing the HTML content to parse.
        col_ids (list of str): A list of column IDs to extract data for.
        companies (list of str): A list of company names to associate with each row of data. 
                                 If provided, each row will include a "company" key with the corresponding company name.
    Returns:
        list of dict: A list of dictionaries where each dictionary represents a row of data.
                      Each dictionary contains keys corresponding to `col_ids` and optionally a "company" key.
                      The values are extracted from the HTML content or set to None if not found.
    """
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

def save_to_csv(data_list, filename) -> None:
    df = pd.DataFrame(data_list)
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def main(input_folder, output_path) -> None: 
    """
    Main function to process webarchive files, extract content, and save the data to CSV files.
    
    
    Arguments:
        input_folder (str): The path to the input folder containing the "webarchives" directory.
        output_path (str): The path to the output directory where the processed CSV files will be saved.

    Raises:
        FileNotFoundError: If the input folder or required files are not found.
        Exception: For any errors during file processing or data extraction.
    """

    webarchive_path = os.path.join(input_folder, "webarchives")
    print(input_folder)
    files = glob.glob(os.path.join(webarchive_path, '*.webarchive'))
    
    for file in files:
        div = "company_info" if "company" in file else "funding"
        html_path = os.path.join(os.getcwd(), "extracted_info.html")
        extract_content(file, html_path)

        with open(html_path, 'rb') as html_file:
            html_content = html_file.read()
            soup = BeautifulSoup(html_content, 'html.parser')
        
        table_headers = get_table_headers(soup)
        companies = get_companies_list(soup)
        col_ids = santize_cols(table_headers)
        data = get_table_content(soup, col_ids, companies)
        
        save_to_csv(data, f"{output_path}/uncleaned_outputs/{div}/pb_uncleaned.csv")
        os.remove(html_path)

def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--input_path", "-i", required=True, help="Input Path to the Webarchives root folder.")
    parser.add_argument("--output_path", "-o", required=True, help="Input Path to the Webarchives root folder.")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.input_path, args.output_path)
