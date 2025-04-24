import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher

def partial_match(string1, string2, threshold=0.8):
    """
    Check if two strings partially match based on a similarity threshold.
    """
    if not isinstance(string1, str) or not isinstance(string2, str):
        return False
    return SequenceMatcher(None, string1.lower(), string2.lower()).ratio() >= threshold

def filter_articles(companies_file, articles_file, start_date, end_date, threshold=0.8):
    # Load the companies and articles data
    companies_df = pd.read_csv(companies_file)
    articles_df = pd.read_csv(articles_file)

    # Convert date strings to datetime objects for filtering
    articles_df['Release Date'] = pd.to_datetime(articles_df['Release Date'], errors='coerce')

    # Filter articles by date range
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    articles_df = articles_df[(articles_df['Release Date'] >= start_date) & (articles_df['Release Date'] <= end_date)]

    # Prepare the lists of company names and entrepreneur names
    companies_list = companies_df['Company Name'].tolist()
    entrepreneurs_list = companies_df['Entrepreneur Name'].dropna().tolist()

    # Filter articles based on matches
    filtered_articles = []
    for _, article in articles_df.iterrows():
        related_companies = article['Related Companies'].split(', ') if pd.notna(article['Related Companies']) else []
        people_mentioned = article['People Mentioned'].split(', ') if pd.notna(article['People Mentioned']) else []
        organizations_mentioned = article['Organizations Mentioned'].split(', ') if pd.notna(article['Organizations Mentioned']) else []

        # Initialize match details
        match_type = None
        match_value = None

        # Check for exact or partial matches
        for company in companies_list:
            if company in related_companies:
                match_type = "Related Company"
                match_value = company
                break
            if any(partial_match(company, org, threshold) for org in organizations_mentioned):
                match_type = "Organization"
                match_value = company
                break

        for entrepreneur in entrepreneurs_list:
            if any(partial_match(entrepreneur, person, threshold) for person in people_mentioned):
                match_type = "Entrepreneur"
                match_value = entrepreneur
                break

        # Add the article only if a match is found
        if match_type:
            article_data = article.to_dict()
            article_data['Match Type'] = match_type
            article_data['Match Value'] = match_value
            filtered_articles.append(article_data)

    # Convert the filtered articles back to a DataFrame
    filtered_df = pd.DataFrame(filtered_articles)

    return filtered_df

def main():
    # Input files
    companies_file = 'test.csv'
    articles_file = 'relevant_articles.csv'

    # Date range for filtering
    start_date = '2024-10-01'
    end_date = '2025-03-31'

    # Partial match threshold
    threshold = 0.8

    # Filter articles
    filtered_df = filter_articles(companies_file, articles_file, start_date, end_date, threshold)

    # Save the filtered articles to a new CSV file
    filtered_df.to_csv('filtered_articles.csv', index=False, encoding='utf-8')
    print("Filtered articles saved to 'filtered_articles.csv'.")

if __name__ == "__main__":
    main()