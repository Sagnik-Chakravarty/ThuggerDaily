import pandas as pd
import requests
from lxml import etree

url = 'https://www.hotnewhiphop.com/search/young%20thug/latest'

headers = {
        'APC':'AfxxVi4F2UA_nrDlCCsAusxsarDFbUjbfuuq1QXL1CFF7shJV-yHTw',
        'receive-cookie-deprecation':'1'
            }

page_text = requests.get(url=url, headers=headers).text
parser = etree.HTMLParser()
# Parse the HTML content
tree = etree.fromstring(page_text, parser)

# Extract articles and their details
articles = []
for item in tree.xpath('//li[contains(@class, "scroller-pages-news-item")]'):
    # Extract title and link
    title_element = item.xpath('.//a[@role="button" and @aria-label]')
    title = title_element[0].get('aria-label').strip() if title_element else None
    link = title_element[0].get('href') if title_element else None

    # Extract description
    description_element = item.xpath('.//span[contains(@class, "inline-block text-sm")]')
    description = description_element[0].text.strip() if description_element else None

    # Extract views
    views_element = item.xpath('.//svg[contains(@class, "fill-gray-700")]/following-sibling::text()[1]')
    views = views_element[0].strip() if views_element else None

    # Extract date
    date_element = item.xpath('.//time/@datetime')
    date = date_element[0] if date_element else None


    #Extract author
    author_element = item.xpath("//a[@class='no-underline ml-2 font-bold text-dark-grey']/@aria-label")
    author = author_element[0] if author_element else None


    articles.append({
        'Title': title,
        'Link': link,
        'Description': description,
        'Views': views,
        'Date': date,
        'Author': author,
    })

# Print the extracted articles
for article in articles:
    print(article)

df = pd.DataFrame(articles)

# Write the DataFrame to a CSV file
csv_file = "HNHH.csv"
df.to_csv(csv_file, index=False)

print(f"Data successfully written to {csv_file}")