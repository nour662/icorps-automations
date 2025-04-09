## 1. Starting Virtual Requirements
source util/myenv/bin/activate

## 2. Installing Dependencies
pip install -r util/requirements.txt --break-system-packages

## 3. Identify Date
tag=$"psum_$(date +%Y-%m-%d)"

## 4. Creating Output Directory
mkdir outputs/outputs_$tag

## 5. Creating Sepereate Directories for Data Sources
cd outputs/outputs_$tag && mkdir usas_batches sam_batches sbir_batches merged_batches log && cd ../..

## 6. Getting cookies.pkl File for SAM.gov login
python3 util/get_cookies.py -u https://sam.gov/ -o sam/cookies.pkl 

## 7. Running SAM.gov Scraper
python3 sam/sam_scraper.py -i inputs/icorps_masterlist.csv -s 0 -o outputs/outputs_$tag

#python3 ../util/merge_batches.py -r outputs/outputs_$tag -s sam

mkdir 

python3 matching_algor.py  

## Matching algorithm for sam 

## run sbir/sttr with name 
##