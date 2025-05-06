import requests
from lxml import html
import pandas as pd
import spacy
import os

# Load spaCy English NLP model
nlp = spacy.load("en_core_web_sm")

# Change this to resume from a specific page
START_PAGE = 0
OUTPUT_FILE = "relevant_articles.csv"

def get_article_links(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    article_urls = tree.xpath('//div[@class= "content"]//a/@href')
    return ["https://www.tedcomd.com" + link for link in article_urls]

def get_content(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    title = tree.xpath('//title')[0].text.strip()
    release_date = tree.xpath('//div[@class="field field--name-field-release-date field--type-datetime field--label-hidden field--item"]/time/text()')
    article_content = ";".join(tree.xpath('//article//text()')).strip()

    article_content = article_content.replace('\n', '')
    lines = [line.strip() for line in article_content.split(';') if line.strip()]
    cleaned_content = ' '.join(lines)

    related_companies = tree.xpath('//div[@class="field field--name-field-company field--type-entity-reference field--label-hidden field--item"]//a/text()')
    related_funds = tree.xpath('//div[@class="field field--name-field-fund field--type-entity-reference field--label-hidden field--items"]//a/text()')

    return {
        "title": title,
        "release_date": release_date[0] if release_date else '',
        "article_content": cleaned_content,
        "related_companies": ', '.join(related_companies),
        "related_funds": ', '.join(related_funds)
    }

def extract_entities(text):
    doc = nlp(text)
    people = sorted(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))
    orgs = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
    return people, orgs

def main():
    page_number = START_PAGE

    # Check if output file already exists to avoid duplicating headers
    file_exists = os.path.isfile(OUTPUT_FILE)

    while True:
        url = f"https://www.tedcomd.com/news-events/press-releases?page={page_number}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Finished scraping at page {page_number}")
            break

        article_links = get_article_links(url)
        print(f"Found {len(article_links)} articles on page {page_number}")

        if not article_links:
            print("No more articles found.")
            break

        articles_data = []

        for link in article_links:
            data = get_content(link)
            people, orgs = extract_entities(data["article_content"])

            articles_data.append({
                'Title': data["title"],
                'Release Date': data["release_date"],
                'URL': link,
                'Related Companies': data["related_companies"],
                'Related Funds': data["related_funds"],
                'Content': data["article_content"],
                'People Mentioned': ', '.join(people),
                'Organizations Mentioned': ', '.join(orgs)
            })

        # Append to CSV file
        df = pd.DataFrame(articles_data)
        df.to_csv(OUTPUT_FILE, mode='a', header=not file_exists, index=False, encoding='utf-8')
        file_exists = True  # Ensure only the first write includes headers
        print(f"Appended page {page_number} to {OUTPUT_FILE}")

        page_number += 1

if __name__ == "__main__":
    main()
