## 1. Setting up Environment Variables
tag="psu_incubator_$(date +%Y-%m-%d)"
output_folder="outputs/outputs_$tag"
inputs_folder="$output_folder/inputs"
input_file="psu_incubator_companies.csv"
general_log="$output_folder/log/general_log.txt"

## 5. Starting Virtual Environment
source util/env/bin/activate >> $general_log
echo "Virtual environment activated" >> $general_log

## 11. Running Matching Algorithm for SAM.gov 
echo "Starting matching algorithm for SAM.gov" >> $general_log
python3 sam/matching_algor.py -i $inputs_folder/$input_file -d $output_folder/uncleaned_outputs/sam_uncleaned.csv -o $inputs_folder

