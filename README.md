# UMD's I-Corps "Where Are They Now (WATN)" Data Collection Scripts

## Scripts
### LinkedIn Script (linkedin_scraper.py)

### Sam.gov Scripts
#### sam_gov_selenium.py
The purpose of the sam_gov_selenium.py script is to search the sam.gov online government database for companies information. The script searches for company information is based on a broad search by company name. 

The company name's are taken in from an external .csv file named "input.csv". The inputted company name's are cleaned in order to insure consistency. This is done through the removing of any company title such as  "Inc", "LLC","Corp", as well as any punctuation. After the company names have been cleaned, they are ran through the database at the rate of 20 at a time in order to limit any loss in the event of a crash. After each batch of 20 ran through the database, the results are outputted.

The program outputs company information in the following order:
'''
keyword,legal_name,num_uei,cage,physical_address,mailing_address,entity_url,start_date,contact1,contact2,
state_country_incorporation,congressional_district
'''
If a company name returns multiple results on the sam.gov database, all results will appear in outputted .csv files. This occurs due to company name not being a unique search term. The results will appear as .csv files named "batch_1.csv", "batch_2.csv", ect. 

Each of these outputted files will need to be cleaned to determine which record is the correct one for the company of interest. To assist in the cleaning process, it is recommend to use the "merging.py" script following this program to combine all batches into a 
large .csv file. 

#### merging.py

### SBIR Scripts
#### sbir_sttr_name_search.py
The purpose of the sbir_sttr_name_search.py is to search sbir.gov online government database for company information and funding information by searching by companies name. 

This script takes in the companies name through the use of an input .csv file named "input.csv". The program reads the input file in groups of 10, rather than the whole file, to limit the loss of data in an event of a crash. If the program did crash, it could be restarted at the latest batch to improve efficiency and reduce the redundency of running the performed batches again. After each batch is run, 2 output .csv files are created: "company_info_sbirsttr_db.csv" and "sbirsttr_funding.csv". 

1. company_info_sbirsttr_db.csv: This file contains information from the company profile, including address, search term, number of employees, website, and more. Additional data points from each company profile can be pulled, so feel free to customize the script according to your needs. The format of the output is as follows: 
'''
Keyword,Name,Street Address,City,State,Zip Code,Website,Employee Count,UEI,SBIR Profile Link
'''

2. sbirsttr_funding.csv: his file includes the SBIR/STTR funding records associated with each company. It contains data such as the search term, start date, end date, funding amount, contract number, solicitation number, and more. You can also customize which data points are included in this file. The format of the output is as follows: 
'''
Keyword Search,Company Name,Start Date,End Date,Funding Amount,Phase,Program,Solicitation Number,Source Link
'''

When searching by company name, multiple records per keyword search may appear and will be represented in the output  .csv files. This allows for a broader search. The outputted files will required cleaning to identify which results are the correct ones. The cleaning process could be eliminated if a unique search term is utilized, such as Unique Entity ID (UEI) or DUNS Number, instead of company name.

#### sbir_sttr_uei_search.ipynb
The sbir_sttr_uei_search.ipynb script is very similiar to the sbir_sttr_name_search.py program. The purpose of this script is to  search sbir.gov online government database for company information and funding information by searching by Unique Entity ID (UEI). By searching using a unique identifier, it is a much more focused search and the data derived from it does not require cleaning. 

Similiar to the other SBIR Script, this program takes in UEI Numberes through the use of an input .csv file named "input.csv". The program reads the input file in groups of 10, rather than the whole file, to limit the loss of data in an event of a crash. If the program did crash, it could be restarted at the latest batch to improve efficiency and reduce the redundency of running the performed batches again. After each batch is run, 2 output .csv files are created: "company_info_sbirsttr_db.csv" and "sbirsttr_funding.csv". 

1. company_info_sbirsttr_db.csv: This file contains various pieces of information from the company profile. The format of the output is as follows: 
'''
Keyword,Name,Street Address,City,State,Zip Code,Website,Employee Count,UEI,SBIR Profile Link
'''

2. sbirsttr_funding.csv: his file includes the SBIR/STTR funding records associated with each company. The format of the output is as follows: 
'''
Keyword Search,Company Name,Start Date,End Date,Funding Amount,Phase,Program,Solicitation Number,Source Link
'''

### USA Spending Scripts
#### usas_scraper.py
The usas_scraper.py script is used to search across the USA Spending database to locate companies information and collection of funding from government entities.

This program uses UEI as a search term and takes it in as input from a .csv file named "input.csv". The program takes in UEI's in groups of 2 to limit loss in the event of program crash. If the program did ever end up crashing, it could be restarted at the batch it left off at. After each batch is run, a .csv file is outputted with each company's information. The information within each output is as follows:
'''
keyword,legal_name,uei,legacy_duns,cage,full_address,congressional_district
'''
For storage purposes, it is recommend to utilize the "merging.py" script to merge together all batches into a large master file. 

While the script is running, it will pull each companies documents off the USA spending website. Upon the scripts completion, it will merge together the 4 different types of filling based on type into 4 different master folders.  The names of the outputted merged .csv files are as follows:
    - assistance_prime_award.csv
    - assistance_sub_award.csv
    - contract_prime_award.csv
    - coontract_sub_award.csv


When the script is completed, 4 seperate .csv files are created

#### funding_merger.py



