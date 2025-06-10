#!/bin/bash
set -e

## 1. Setting up Environment Variables
root_tag="WATN_input_group_1"
tag="${root_tag}_$(date +%Y-%m-%d)"
output_folder="outputs/outputs_$tag"
inputs_folder="$output_folder/inputs"
input_file="$root_tag.csv"
general_log="$output_folder/log/general_log.txt"

## 2. Creating Output Directories
mkdir -p "$output_folder"
mkdir -p "$inputs_folder"

## 3. Creating Separate Directories for Data Sources
mkdir -p "$output_folder"/{usas_batches,sam_batches,sbir_batches,uncleaned_outputs,cleaned_outputs,log}
echo "Log directory created at $output_folder/log" >> "$general_log"

## 4. Copy Inputs and Clean Up Extras
find all_inputs/ -type f -exec cp {} "$inputs_folder" \;

for file in "$inputs_folder"/*; do
  if [[ ! $(basename "$file") =~ ^$root_tag ]]; then
    rm -f "$file"
  fi
done

if [ -d "all_inputs/webarchives/$root_tag" ]; then
    mkdir -p "$inputs_folder/webarchives"
    cp -r all_inputs/webarchives/"$root_tag"/. "$inputs_folder/webarchives"
fi

## 5. Starting Virtual Environment
python3 -m venv util/env
source util/env/bin/activate >> $general_log
echo "Virtual environment activated" >> $general_log

## 6. Installing Dependencies
pip3 install --upgrade pip >> $general_log
echo "pip3 upgraded to the latest version" >> $general_log
pip3 install -r util/requirements.txt >> $general_log
echo "Dependencies installed" >> $general_log

## 7. Running UEI search by DUNS, if applicable 
echo "Starting UEI search by DUNS" >> $general_log
python3 sbir/duns_search.py -i $inputs_folder/$input_file -o $output_folder
echo "UEI search by DUNS completed" >> $general_log

## 8. Getting cookies.pkl File for SAM.gov login
python3 util/get_cookies.py -u https://sam.gov/ -o sam/cookies.pkl 
echo "Cookies.pkl file created at sam/cookies.pkl" >> $general_log

## 9. Running SAM.gov Scraper
echo "Starting SAM.gov scraper" >> $general_log
python3 sam/sam_scraper.py -i $inputs_folder/$input_file -o $output_folder
echo "SAM.gov scraper completed" >> $general_log

## 10. Running Batch Merger for SAM.gov
echo "Starting batch merger for SAM.gov" >> $general_log
python3 util/merge_batches.py -r $output_folder -s sam -o $output_folder
echo "Batch merger for SAM.gov completed" >> $general_log

## 11. Running Matching Algorithm for SAM.gov 
echo "Starting matching algorithm for SAM.gov" >> $general_log
python3 sam/matching_algor.py -i "$inputs_folder/$input_file" -o $output_folder -d "$output_folder/uncleaned_outputs/company_info/sam_uncleaned.csv" 
echo "Matching algorithm for SAM.gov completed" >> $general_log

## 12. Running SBIR/STTR Scraper 
echo "Starting SBIR/STTR scraper" >> $general_log
python3 sbir/sbir_scraper.py -i $inputs_folder/$input_file -s 0 -o $output_folder
echo "SBIR/STTR scraper completed" >> $general_log

## 13. Running Batch Merger for SBIR/STTR
echo "Starting batch merger for SBIR/STTR" >> $general_log
python3 util/merge_batches.py -r $output_folder/sbir_batches -s sbir_awards  -o $output_folder
python3 util/merge_batches.py -r $output_folder/sbir_batches -s sbir_company_info -o $output_folder
echo "Batch merger for SBIR/STTR completed" >> $general_log

# 14. Removing SBIR Batch File 
echo "Removing SBIR batch file" >> $general_log 
rm -rf $output_folder/sbir_batches
echo "SBIR batch file removed" >> $general_log

#15. Running USAS Scraper
echo "Starting USAS scraper" >> $general_log
python3 usas/usas_api.py -i $inputs_folder/$input_file -o $output_folder
echo "USAS scraper completed" >> $general_log

#16. Running Batch Merger for USAS
echo "Starting batch merger for USAS" >> $general_log
python3 util/merge_batches.py -r $output_folder/usas_batches -s usas_grants  -o $output_folder
python3 util/merge_batches.py -r $output_folder/usas_batches -s usas_contracts  -o $output_folder
python3 util/merge_batches.py -r $output_folder/usas_batches -s usas_company_info -o $output_folder
echo "Batch merger for USAS completed" >> $general_log

#17. removing USAS batch file
echo "Removing USAS batch file" >> $general_log
rm -rf $output_folder/usas_batches
echo "USAS batch file removed" >> $general_log


#18. Running Pitchbook Webarchive Scraper
echo "Running Pitchbook Webarchive Scraper" >> $general_log
python3 pitchbook/pb_scraper.py -i $inputs_folder -o $output_folder
echo "Finished Pitchbook Webarchive Scraper" >> $general_log

#19. Cleaning Company Info
echo "Cleaning Company Info" >> $general_log
python3  cleaning_files/clean_company_info.py -i $output_folder -r $root_tag
echo "Cleaning Company Info Done" >> $general_log
