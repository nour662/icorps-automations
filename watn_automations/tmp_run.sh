#!/bin/bash
set -e

## 1. Setting up Environment Variables
root_tag="psu_incubator_companies"
tag="${root_tag}_$(date +%Y-%m-%d)"
tag="psu_incubator_companies_2025-04-22"
output_folder="outputs/outputs_$tag"
inputs_folder="$output_folder/inputs"
input_file="$root_tag.csv"
general_log="$output_folder/log/general_log.txt"






#19. Cleaning Company Info
python3  cleaning_files/clean_company_info.py -i $output_folder -r $root_tag
