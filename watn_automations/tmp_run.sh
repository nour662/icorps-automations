#!/bin/bash
set -e

## 1. Setting up Environment Variables
root_tag="hub-2025-g1"
tag="${root_tag}_$(date +%Y-%m-%d)"
output_folder="outputs/$tag"
inputs_folder="$output_folder/inputs"
input_file="$root_tag.csv"
general_log="$output_folder/log/general_log.txt"






#19. Cleaning Company Info
echo "Merging Company Info" >> $general_log
python3 cleaning_files/merge_company_info.py -i $inputs_folder/$input_file -d $output_folder/cleaned_outputs/company_info -o $output_folder/finalized_results
echo "Finished Merging Company Info" >> $general_log
