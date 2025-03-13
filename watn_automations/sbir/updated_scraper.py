import requests

def search_awards_by_uei(uei):
    """Fetch SBIR awards based on UEI."""
    url = f"https://api.www.sbir.gov/public/api/awards?uei={uei}"
    response = requests.get(url)

    print(f"Request URL: {url}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        try:
            awards = response.json()
            print(f"Response Data: {awards}")  # Debugging: Print full response
            return awards
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            return None
    else:
        print(f"Error fetching data: {response.text}")
        return None

def extract_company_info(awards, uei):
    """Extracts company details from the award data and ensures correct UEI."""
    for award in awards:
        if award.get("uei") == uei:  # Ensure the returned data matches the requested UEI
            return {
                "Company Name": award.get("firm"),
                "UEI": award.get("uei"),
                "DUNS": award.get("duns"),
                "Number of Employees": award.get("number_employees"),
                "HUBZone Owned": award.get("hubzone_owned"),
                "Women Owned": award.get("women_owned"),
                "Socially/Economically Disadvantaged": award.get("socially_economically_disadvantaged"),
                "Company URL": award.get("company_url"),
                "Address": f"{award.get('address1')} {award.get('address2')}".strip(),
                "City": award.get("city"),
                "State": award.get("state"),
                "ZIP Code": award.get("zip"),
                "POC Name": award.get("poc_name"),
                "POC Title": award.get("poc_title"),
                "POC Phone": award.get("poc_phone"),
                "POC Email": award.get("poc_email"),
            }
    
    print(f"No matching company found for UEI: {uei}")  # Debugging
    return None  # Return None if no match is found

def extract_funding_info(awards):
    """Extracts award funding details."""
    return [
        {
            "Award Title": award.get("award_title"),
            "Agency": award.get("agency"),
            "Branch": award.get("branch"),
            "Phase": award.get("phase"),
            "Award Year": award.get("award_year"),
            "Award Amount": award.get("award_amount"),
            "Contract Number": award.get("contract"),
            "Proposal Award Date": award.get("proposal_award_date"),
            "Contract End Date": award.get("contract_end_date"),
            "Abstract": award.get("abstract"),
        }
        for award in awards
    ]

# Input UEI
uei = "LA9LCVM7HMK5"

# Fetch awards
awards = search_awards_by_uei(uei)

if awards:
    company_info = extract_company_info(awards, uei)
    funding_info = extract_funding_info(awards)

    if company_info:
        print("\n=== Company Information ===")
        for key, value in company_info.items():
            print(f"{key}: {value}")
    else:
        print("\nNo company information found for the given UEI.")

    """ print("\n=== Funding Details ===")
    for funding in funding_info:
        print("\n--- Award ---")
        for key, value in funding.items():
            print(f"{key}: {value}")"""
