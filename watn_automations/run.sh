source ../util/myenv/bin/activate
today=$(date +"%m%d%Y")

rm -R outputs/outputs_$today



mkdir outputs/outputs_$today

cd outputs/outputs_$today

mkdir usas_batches sam_batches sbir_batches log merged_files 

cd ../..

#python3 get_cookies.py -i https://sam.gov  -o ../watn_automations/sam/cookies.pkl

python3 sam/sam_scraper.py -i inputs/icorps_masterlist.csv -s 0 -o outputs/outputs_$today

#python3 ../util/merge_batches.py -r outputs/outputs_$today -s sam


## Matching algorithm for sam 

## run sbir/sttr with name 
##