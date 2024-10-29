import os
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_file_content(driver, file_url, download_path, file_name):
    try:
        driver.execute_script("window.open(arguments[0], '_blank');", file_url)
        driver.switch_to.window(driver.window_handles[1])
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))  # Wait for body tag to ensure the page is loaded
        )

        file_content = driver.find_element(By.TAG_NAME, 'body').text

        with open(os.path.join(download_path, file_name), 'w') as f:
            f.write(file_content)
        
        print(f"Saved content for {file_name}")

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
    except Exception as e:
        print(f'Error while extracting content from {file_url}: {e}')

def download_data(driver, download_path): 
    try: 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="Index of /threds/active/data/backup"]'))
        )

        # Find all file elements that match the .txt format
        file_elements = driver.find_elements(By.XPATH, '//a[contains(@href, ".txt")]')
        files = {}

        # Pattern for file name format: userID_timestamp.txt
        pattern = r'([A-Za-z0-9]+)_(\d+)\.txt'

        for file_element in file_elements:
            file_name = file_element.text
            match = re.match(pattern, file_name)
            
            if match:
                user_id = match.group(1)
                timestamp = int(match.group(2))
                
                # Store only the most recent file per userID
                if user_id not in files or timestamp > files[user_id]['timestamp']:
                    files[user_id] = {
                        'file_name': file_name,
                        'timestamp': timestamp,
                        'element': file_element
                    }

        # Open each most recent file by user ID in a new tab
        for user_id, file_info in files.items():
            file_url = file_info['element'].get_attribute('href')
            extract_file_content(driver, file_url, download_path, file_info['file_name'])

    except Exception as e: 
        print(f'Error Message: {e}')

def parse_txt_files(download_path):
    for file_name in os.listdir(download_path):
        if file_name.endswith('.txt'):
            user_id = file_name.split('_')[0]  # Extract user ID from file name
            file_path = os.path.join(download_path, file_name)
            with open(file_path, 'r') as file:
                content = file.read()

            # Parse Decisions
            decisions_section = re.search(r'Decision Number.*?(?=Team Member Type,)', content, re.DOTALL)
            if decisions_section:
                decisions_data = decisions_section.group(0).strip().splitlines()
                # Write decisions to CSV
                with open(os.path.join(download_path, f'decisions_{user_id}.csv'), 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    for line in decisions_data[1:]:  # Skip the header
                        csv_writer.writerow(line.split(','))
                print(f'Saved decisions data for {file_name}')
            else:
                print(f'No decisions section found in {file_name}')

            # Parse Team Members
            team_members_section = re.search(r'Team Member Type.*?(?=Utility,)', content, re.DOTALL)
            if team_members_section:
                team_members_data = team_members_section.group(0).strip().splitlines()
                # Write team members to CSV
                with open(os.path.join(download_path, f'team_members_{user_id}.csv'), 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    for line in team_members_data[1:]:  # Skip the header
                        csv_writer.writerow(line.split(','))
                print(f'Saved team members data for {file_name}')
            else:
                print(f'No team members section found in {file_name}')

            # Parse Utility
            utility_section = re.search(r'Utility.*?(?=Room Name,)', content, re.DOTALL)
            if utility_section:
                utility_data = utility_section.group(0).strip().splitlines()
                # Write utility to CSV
                with open(os.path.join(download_path, f'utility_{user_id}.csv'), 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    for line in utility_data[1:]:  # Skip the header
                        csv_writer.writerow(line.split(','))
                print(f'Saved utility data for {file_name}')
            else:
                print(f'No utility section found in {file_name}')

            # Parse Timing
            timing_section = re.search(r'Room Name.*?(?=info_Responses)', content, re.DOTALL)
            if timing_section:
                timing_data = timing_section.group(0).strip().splitlines()
                # Write timing to CSV
                with open(os.path.join(download_path, f'timing_{user_id}.csv'), 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    for line in timing_data[1:]:  # Skip the header
                        csv_writer.writerow(line.split(','))
                print(f'Saved timing data for {file_name}')
            else:
                print(f'No timing section found in {file_name}')


def main(): 
    download_path = os.path.join(os.getcwd(), "downloads")  # Set your download path
    os.makedirs(download_path, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "safebrowsing.enabled": True  # Bypass safe browsing check
    })

    # Initialize Chrome WebDriver with specified options
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try: 
        driver.get("https://cie.psu.edu/threds/active/data/backup/?C=M;O=D")
        
        # Call the download_data function to download the most recent files
        #download_data(driver, download_path)

        # After downloading the files, parse them into CSVs
        parse_txt_files(download_path)

    except Exception as e: 
        print(f'Error message: {e}')

    finally: 
        driver.quit()

if __name__ == "__main__": 
    main()
