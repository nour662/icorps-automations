#!/bin/bash
set -e

## 1. Setting up Environment Variables
root_tag="psu_incubator_companies"
tag="${root_tag}_$(date +%Y-%m-%d)"
output_folder="outputs/outputs_$tag"
inputs_folder="$output_folder/inputs"
input_file="$root_tag.csv"
general_log="$output_folder/log/general_log.txt"


########################################################################


## 9. Running SAM.gov Scraper
echo "Starting SAM.gov scraper" >> $general_log
python3 sam/sam_scraper.py -i $inputs_folder/$input_file -o $output_folder -hd False
echo "SAM.gov scraper completed" >> $general_log

## 10. Running Batch Merger for SAM.gov
echo "Starting batch merger for SAM.gov" >> $general_log
python3 util/merge_batches.py -r $output_folder -s sam -o $output_folder
echo "Batch merger for SAM.gov completed" >> $general_log

## 11. Running Matching Algorithm for SAM.gov 
echo "Starting matching algorithm for SAM.gov" >> $general_log
python3 sam/matching_algor.py -i "$inputs_folder/$input_file" -o $output_folder -d "$output_folder/uncleaned_outputs/company_info/sam_uncleaned.csv" 
echo "Matching algorithm for SAM.gov completed" >> $general_log
