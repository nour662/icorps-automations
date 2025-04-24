## General

def get_state_abbreviations():
    state_abbreviations = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
    "Virgin Islands": "VI", "Puerto Rico": "PR"
    }
    
    return state_abbreviations



## For Funding Info
def get_funding_final_cols(): 
    cols = [
    "Account Name", ## Original company name on file
    "Date Awarded", ## Date of award
    "Award Amount", ## Funding Amount
    "Funding Source", ## Funding Source (Angel, VC, Frederal, Grant, MIPS, NIH, NSF I-Corps, Other, SBIR, Series, STTR, TEDCO)
    "Funding Stage", ## Funding Type (Pre-Seed, Seed, Series A, Series B, Series C, Series D)
    "Source Website" ## Source Website
    "Award Start Date", ## Award Start Date
    "Award End Date", ## Award End Date
    "Award Number", ## Award Number
    "Additional Info", ## Additional Information
    ]
    return cols



## For Company Info 
def get_compinfo_final_cols(): 
    cols = [
    "Account Name", ## Original company name on file
    "Legal Name", ## Legal Company Name
    "UEI", ## UEI
    "DUNS", ## DUNS Number
    "CAGE", ## CAGE Code
    "Company Exists", ## Does the company exist?
    "Active",  ## Is the copany active? 
    "Company Website", ## Company Website
    "Employees", ## Number of employees
    "Street Address", ## Street Address
    "City", ## City
    "State", ## State
    "Zip Code", ## Zip Code     
    "Country", ## Country
    "Legislative District", ## Legislative District
    "Industry", ## Industry     
    "Annual Revenue Range", ## Annual Revenue Range
    #"Merged", ## Has the company been aqquired or been a part of a merger?
    #"Merger Additional Info", ## Additional information about the merger
    "Incorporation Date", ## Date of 
    "Incorporation Year", ## Year of incorporation
    "Incorporation State", ## State of incorporation
    "Incorporation Country", ## Country of incorporation 
    "Incorporation Type", ## Type of incorporation
    "Description" ## Description
    ]

    return cols 

def get_sam_compinfo_col_mapping(): 
    company_info_cols_mapping = {

    "legal_name": "Legal Name",
    "num_uei": "UEI",
    "cage": "CAGE",
    "street" : "Street Address",
    "city" : "City",
    "state" : "State",
    "zip_code" : "Zip Code",
    "country" : "Country",
    "entity_url" : "Company Website",
    "start_date" : "Incorporation Date",
    "incorporation_state" : "Incorporation State",
    "incorporation_country" : "Incorporation Country",
    "congressional_district" : "Legislative District",}

    return company_info_cols_mapping

def get_sbir_compinfo_col_mapping(): 

    company_info_cols_mapping = {
    "UEI": "UEI",
    "Street Address" : "Street Address",
    "City" : "City",
    "State" : "State",
    "Zip Code" : "Zip Code",
    "Website" : "Company Website"
    }
    return company_info_cols_mapping

def get_usas_compinfo_col_mapping(): 
    company_info_cols_mapping = {
    "uei": "UEI",
    "duns" : "DUNS",
    "address" : "Street Address",
    "city" : "City",
    "state" : "State",
    "zip" : "Zip Code",
    "congressional_district" : "Legislative District"
    
    }
    return company_info_cols_mapping

def get_pb_compinfo_col_mapping(): 
    company_info_cols_mapping = {
    "Company": "Account Name",
    "hqCity": "City",
    "hqState": "State",
    "hqAddressLine1": "Street Address",
    "primaryIndustrySector": "Industry",
    "revenue" : "Annual Revenue Range",
    "legalName": "Legal Name",
    "description": "Description",
    "employees": "Employees",
    "yearFounded": "Incorporation Year",
    "companyWebsite": "Company Website",
    "businessStatus" : "Status"
    }
    return company_info_cols_mapping










