## 1. Starting Virtual Requirements
source util/myenv/bin/activate

## 2. Installing Dependencies
pip install -r util/requirements.txt --break-system-packages

## 3. Identify Date
today=$(date +"%m%d%Y")

## 4. Creating Output Directory
mkdir outputs/outputs_$today

## 5. Creating Sepereate Directories for Data Sources
cd outputs/outputs_$today && mkdir usas_batches sam_batches sbir_batches merged_batches && cd ../..

## 6. Getting cookies.pkl File for SAM.gov login
python3 util/get_cookies.py -i https://sam.gov  -o sam/cookies.pkl 

## 7. Running SAM.gov Scraper
python3 sam/sam_scraper.py -i inputs/icorps_masterlist.csv -s 0 -o outputs/outputs_$today

#python3 ../util/merge_batches.py -r outputs/outputs_$today -s sam

mkdir 

python3 matching_algor.py  

## Matching algorithm for sam 

## run sbir/sttr with name 
##