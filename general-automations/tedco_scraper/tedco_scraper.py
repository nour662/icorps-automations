import requests
from lxml import html
import openai
import pandas as pd
import csv
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_article_links(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    article_urls = tree.xpath('//div[@class= "content"]//a/@href')
    return article_urls

def get_content(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    title = tree.xpath('//title')[0].text.strip()
    release_date = tree.xpath('//div[@class="field field--name-field-release-date field--type-datetime field--label-hidden field--item"]/time/text()')
    article_content = ";".join(tree.xpath('//article//text()')).strip()

    # Remove line breaks from the article content
    article_content = article_content.replace('\n', '')

    # Cleaning up and formatting the article content
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

def check_relevance(article_content, companies_list):

    prompt = f"Is the following article relevant to any of these companies or entrepreneurs: {', '.join(companies_list)}?\n\nArticle: {article_content}\n\nRespond with 'Yes' or 'No'."

    # Call OpenAI API
    response = openai.Completion.create(
        engine="text-embedding-ada-002",
        prompt=prompt,
        max_tokens=5
    )

    return response.choices[0].text.strip().lower() == "yes"

def main():
    companies_df = pd.read_csv('companies.csv')
    companies_list = companies_df['Company Name'].tolist()
    companies_list = [str(a) for a in companies_list]

    relevant_articles = []

    page_number = 0

    while True:
        main_url = f"https://www.tedcomd.com/news-events/press-releases?page={page_number}"
        response = requests.get(main_url)

        if response.status_code != 200:
            print(f"Bad request encountered for page {page_number}, stopping scraping.")
            break

        tree = html.fromstring(response.content)
        article_links = tree.xpath('//div[@class= "content"]//a/@href')
        article_links = [f"https://www.tedcomd.com{link}" for link in article_links]

        for link in article_links:
            data = get_content(link)
            if data:
                is_relevant = check_relevance(data["article_content"], companies_list)
                if is_relevant:
                    relevant_articles.append({
                        'Title': data["title"],
                        'Release Date': data["release_date"],
                        'Related Companies': data["related_companies"],
                        'Related Funds': data["related_funds"],
                        'URL': link,
                        'Content': data["article_content"]
                    })

        page_number += 1

    relevant_df = pd.DataFrame(relevant_articles)
    relevant_df.to_csv('relevant_articles.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    main()
