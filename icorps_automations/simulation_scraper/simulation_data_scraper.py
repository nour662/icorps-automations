import os
import re
import csv
import pandas as pd
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
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
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
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="Index of /threds/active/data/backup"]'))
        )

        file_elements = driver.find_elements(By.XPATH, '//a[contains(@href, ".txt")]')
        files = {}

        pattern = r'([A-Za-z0-9]+)_(\d+)\.txt'

        for file_element in file_elements:
            file_name = file_element.text
            match = re.match(pattern, file_name)

            if match:
                user_id = match.group(1)
                timestamp = int(match.group(2))

                if user_id not in files or timestamp > files[user_id]['timestamp']:
                    files[user_id] = {
                        'file_name': file_name,
                        'timestamp': timestamp,
                        'element': file_element
                    }

        for user_id, file_info in files.items():
            file_url = file_info['element'].get_attribute('href')
            extract_file_content(driver, file_url, download_path, file_info['file_name'])

    except Exception as e:
        print(f'Error Message: {e}')


def parse_txt_files(download_path):
    decision_columns = [
        "User ID", "Timestamp", "Decision Number", "Timestamp_g", "Time Interval", "Category", "Budget Cost Level",
        "Budget Cost Amount", "Time Cost Units", "Time Cost Level", "Time Cost Amount", "Part Type",
        "Part Level", "Part Utility", "Team Member Type", "Team Effect Type", "Team Discount Amount",
        "Team Unlock Type", "Funding Type", "Funding Level", "Funding Award Amount", "Interest Percentage",
        "Interest Amount", "Equity Amount", "Funding Hit Rate", "Funding Successful", "Feedback Level",
        "Global Market Level", "Networking Type", "Networking Level"
    ]

    game_stats_columns = [
        "User ID", "Timestamp", "Decisions Count", "Remaining Budget", "Remaining Time", "Device Utility",
        "Part01 Level", "Part 02 Level", "Part 03 Level", "Interest Per Month", "Equity Amount",
        "Customer Feedback Level", "Global Market Level", "Main Lobby", "R&D", "Customer Discovery Room",
        "Hiring Office", "Funding Office", "Networking Room", "Design Consultant", "Design Expert", "Manufacturing Engineer",
        "Business Advisor"
    ]

    decisions_data = []
    game_stats_data = []

    for file_name in os.listdir(download_path):
        if file_name.endswith('.txt'):
            user_id, timestamp = file_name.split('_')[0], file_name.split('_')[1].replace(".txt", "")
            file_path = os.path.join(download_path, file_name)

            with open(file_path, 'r') as file:
                content = file.read()

            stats = re.search(r"Decisions Count,Remaining Budget,Remaining Time,Device Utility,Part01 Level,Part 02 Level,Part 03 Level,Interest Per Month,Equity Amount,Customer Feedback Level,Global Market Level,\s*([\s\S]*?)(?=\n\n|\Z)", content)
            if stats:
                stats_values = [value.strip() for value in stats.group(1).strip().split(',')][0:-1]
                game_row = [user_id, timestamp] + stats_values

                room_names = ["Main Lobby", "R&D", "Customer Discovery Room", "Hiring Office", "Funding Office", "Networking Room"]
                
                for room in room_names:
                    room_time = re.search(rf"{room},\s*([\d.]+)", content)
                    game_row.append(float(room_time.group(1)) if room_time else 0)  

                game_stats_data.append(game_row)
            else:
                print(f"No game stats found in {file_name}")

            team_types_section = re.search(r"Team Member Type,Effect Type,Effect Amount,Unlock Type,\s*([\s\S]*?)(?=\n\n|\Z)", content)
            if team_types_section:
                team_types_text = team_types_section.group(1).strip()
                team_types = []
                for line in team_types_text.splitlines():
                    parts = line.split(',')
                    if len(parts) > 0:
                        team_type = parts[0].strip()
                        if team_type.startswith("TYPE_"):
                            team_types.append(team_type)

                game_row.extend([
                    1 if "TYPE_01" in team_types else 0,
                    1 if "TYPE_02" in team_types else 0,
                    1 if "TYPE_03" in team_types else 0,
                    1 if "TYPE_04" in team_types else 0
                ])
                print(game_row)
            else:
                print(f"No Team Member Types section found in {file_name}")
                game_row.extend([None, None, None, None]) 

            decisions = re.search(r"Decision Number,Timestamp,Time Interval,Category,Budget Cost Level,Budget Cost Amount,Time Cost Units,Time Cost Level,Time Cost Amount,Part Type,Part Level,Part Utility,Team Member Type,Team Effect Type,Team Discount Amount,Team Unlock Type,Funding Type,Funding Level,Funding Award Amount,Interest Percentage,Interest Amount,Equity Amount,Funding Hit Rate,Funding Successful,Feedback Level,Global Market Level,Networking Type,Networking Level,\s*([\s\S]*?)(?=\n\n|\Z)", content)
            if decisions:
                for row in decisions.group(1).strip().splitlines():
                    decision_row = [user_id, timestamp] + [value.strip() for value in row.split(',')][0:-1]
                    decisions_data.append(decision_row)
            else:
                print(f"No decisions found in {file_name}")


    decisions_df = pd.DataFrame(decisions_data, columns=decision_columns)
    game_stats_df = pd.DataFrame(game_stats_data, columns=game_stats_columns)

    decisions_df.to_csv(os.path.join(download_path, "../output/decisions.csv"), index=False)
    game_stats_df.to_csv(os.path.join(download_path, "../output/game_stats.csv"), index=False)

    print("CSV files generated for decisions and game stats.")


def main():
    download_path = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_path, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://cie.psu.edu/threds/active/data/backup/?C=M;O=D")
        
        download_data(driver, download_path)
        parse_txt_files(download_path)

    except Exception as e:
        print(f'Error message: {e}')

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
