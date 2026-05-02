import time
from re import search, IGNORECASE, compile
import pandas as pd
from anaconda_navigator.utils.url_utils import file_name
from django.utils.lorem_ipsum import paragraphs
from pandas import read_csv
from playwright.sync_api import sync_playwright
from sqlalchemy import column
from beepy import beep

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
'''
AJC- Atlanta Journal Conference
'''

def ajc_news_headline_scrape(search_term,
                             base_url = 'https://www.ajc.com/search/',
                             wait_time = 0.5):
    search_term = '%20'.join(search_term.split(' '))
    url = base_url + search_term
    # Preparing the browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        # declaring variables to store the data
        headlines, pub_date, snippets, links = [], [], [], []

        while True: # while there is a next page button
            # Get the headlines, date, href and snippet
            time.sleep(wait_time)
            headline_element = page.locator('.queryly_item_title')
            date_element = page.locator('.queryly_item_pubdate')
            snippet_element = page.locator('.queryly_item_description')
            href = page.locator('.queryly_item_row')

            art_number = headline_element.count()
            if art_number == 0:
                break

            # Extract data from each article
            for i in range(art_number):
                headline = headline_element.nth(i).text_content()
                date = date_element.nth(i).text_content()
                snippet = snippet_element.nth(i).text_content()

                anchor = href.nth(i).locator('a')
                link = anchor.get_attribute('href')

                headlines.append(headline)
                pub_date.append(date)
                snippets.append(snippet)
                links.append(link)

            # Check if the "next" button exists and navigate to the next page
            nxt_count = page.locator('a.next_btn').count()
            if nxt_count == 0:
                break  # Break the loop if no "next" button is found

            page.click('a.next_btn')
            page.wait_for_selector('.queryly_item_title')

        article_df = pd.DataFrame({'headline': headlines,
                                   'publication_date': pub_date,
                                   'snippet': snippets,
                                   'links': links})

        # Print the dataframe
        print(article_df)

        context.close()
        browser.close()
        beep(sound = 'ping')
        return article_df



def scrape_article(art_url, base_url= 'https://www.ajc.com', headless = False):
    url = base_url + art_url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()

        try:
            page.goto(url, timeout=300000)
            page.wait_for_selector('.story-text', timeout=10000)
            paragraphs = page.locator('.story-text')
            article_content = []
            for i in range(paragraphs.count()):
                paragraph_text = paragraphs.nth(i).inner_text()
                article_content.append(paragraph_text)
            full_article = "\n\n".join(article_content)

        except Exception as e:
            print("failed to scrape article:\t", url)
            full_article = None

        finally:
            context.close()
            browser.close()
    return full_article


def ajc(search_term,
        file_name,
        base_url = 'https://www.ajc.com/search/?query=',
        wait_time = 0.5,
        headless_state=False
        ):
    ar_df = ajc_news_headline_scrape(base_url = base_url,
                                     search_term = search_term,
                                     wait_time= wait_time)
    art_df = pd.DataFrame()
    filename = file_name + '.csv'
    for i, link in enumerate(ar_df['links']):
        print(link)
        print(f'\nscraped {i} out of {len(ar_df)} completion: {i/len(ar_df)*100}%')
        article = scrape_article(art_url=  link, headless = headless_state)
        df = pd.DataFrame({'article': [article], 'links': [link]})
        art_df = pd.concat([art_df, df])

    ajc = pd.merge(ar_df, art_df, on = 'links', how = 'left')
    ajc.to_csv(filename, index=False)
    pd.set_option('display.max_columns', None)
    print(ajc)
    beep(sound = 'success')
    return ajc


#ajc('yfn lucci', file_name = 'ajc_yfnlucci')
#ajc('ysl', file_name = 'ajc_ysl')
# ajc('ysl rico', file_name = 'ajc_yslrico')
# time.sleep(10)
# ajc('gunna', file_name = 'ajc_gunna')
# time.sleep(10)
# ajc('young thug', file_name = 'ajc_youngthug')


'''
Rolling Stones
'''
# Function to scrape headlines, links, and dates
def scrape_headlines_and_dates():
    # Base URL and search URL
    base_url = 'https://www.rollingstone.com/'
    search_url = 'results/?current=n_1_n&q=YOUNG%20THUG&size=n_100_n&sort-field=date&sort-direction=desc'
    url = base_url + search_url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        # Wait for the first page to load
        page.wait_for_selector('.result-title')

        # Initialize lists to store headlines, links, and dates
        headlines = []
        links = []
        dates = []

        # Loop to click "Next" button 8 times
        for _ in range(8):
            # Scrape all headlines, links, and dates on the current page
            headline_elements = page.locator('.result-title')
            date_elements = page.locator('.icon .fa-calendar')  # Adjust selector if necessary

            for i in range(headline_elements.count()):
                headline = headline_elements.nth(i).text_content().strip()
                link = headline_elements.nth(i).locator('a').get_attribute('href')
                date_element = date_elements.nth(i).locator('..').text_content().strip()  # Get parent span's text

                if headline and link and date_element:
                    headlines.append(headline)
                    links.append(link)
                    dates.append(date_element)

            # Click the "Next" button if it exists
            try:
                next_button = page.locator('[aria-label="Next page"]')
                if next_button.is_visible():
                    next_button.scroll_into_view_if_needed()
                    next_button.click()
                    # Wait for the next page to load
                    page.wait_for_selector('.result-title', timeout=5000)
                else:
                    print("No more pages available.")
                    break
            except Exception as e:
                print(f"Error clicking 'Next' button: {e}")
                break

        # Close the browser
        context.close()
        browser.close()

        # Return scraped data as a DataFrame
        return pd.DataFrame({'Headline': headlines, 'Link': links, 'Date': dates})


# # Call the function and save results to a DataFrame
# df = scrape_headlines_and_dates()
#
# # Save DataFrame to a CSV file (optional)
# df.to_csv('rollingstone_data.csv', index=False)
#
# # Print the DataFrame
# print(df)
def rolling_stone_article(df):
    df = read_csv('rollingstone_data.csv')
    print(df.columns)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        df_art = pd.DataFrame()
        for link in df['Link']:
            time.sleep(0.5)
            try:
                page.goto(link)
                page.wait_for_selector('.pmc-paywall')
                article = page.locator('.pmc-paywall')
                article = article.text_content()
                df = pd.DataFrame({'article': [article], 'links': [link]})
                df_art = pd.concat([df_art, df])

            except Exception as e:
                print("error link not found:\t", link)
                print(e)
                article = None


        context.close()
        browser.close()
        print(df_art)
        df_art.to_csv('rollingstone_article.csv', index=False)

# df_art = pd.read_csv('rollingstone_article.csv')
# df_data = pd.read_csv('rollingstone_data.csv')
# print(df_art.columns)
# print(df_data.columns)
# df = pd.merge(df_art, df_data, how='right', left_on = 'links', right_on='Link')
# df = df.drop('Link', axis=1)
# pd.set_option('display.max_columns', None)
# df.to_csv('rollingstones.csv', index=False)

'''
Washington Post
'''


def washingtonpost_data(search_term, filter_date):
    url = 'https://www.washingtonpost.com/search/?query=' + '+'.join(search_term.split(sep=' '))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()

        # Navigate to the target URL
        page.goto(url)

        # Check if "Load more results" button exists
        try:
            page.wait_for_selector('text=Load more results', timeout=60000)
            next_button = page.locator('text=Load more results')

            # Loop to click the button until it's no longer visible
            while next_button.is_visible():
                try:
                    next_button.scroll_into_view_if_needed()
                    next_button.click()
                    time.sleep(2)  # Wait for new content to load
                except Exception as e:
                    print(f"An error occurred while clicking: {e}")
                    break
        except Exception as e:
            print(f"'Load more results' button not found: {e}")

        # Locate elements for headlines, snippets, dates, and links
        headline_element = page.locator('h2.wpds-c-ggDmLr')
        snippet_date_element = page.locator('div.wpds-c-cywVJb')
        link_element = page.locator('a.wpds-c-EDbBA')

        # Initialize lists to store results
        headlines = []
        snippets = []
        dates = []
        links = []

        # Iterate through all located elements and extract data
        for i in range(headline_element.count()):
            try:
                headline = headline_element.nth(i).text_content().strip()

                # Extract snippet and date from the same parent div
                snippet_date_div = snippet_date_element.nth(i)
                snippet = snippet_date_div.locator('span.wpds-c-fnfACo').text_content().strip()
                date = snippet_date_div.locator('span:nth-child(2)').text_content().strip()

                link = link_element.nth(i).get_attribute('href')

                headlines.append(headline)
                snippets.append(snippet)
                dates.append(date)
                links.append(link)
            except Exception as e:
                print(f"Error processing item {i}: {e}")

        # Create a DataFrame from the extracted data
        df = pd.DataFrame({'headline': headlines, 'snippet': snippets, 'date': dates, 'link': links})

        df['date'] = pd.to_datetime(df['date'], format='%B %d, %Y')
        filter_df = df[df['date'].dt.year >= filter_date]
        df = filter_df.sort_values(by=['date'])

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', None)

        print(df)

        file_name = 'washingtonpost_' + search_term + '.csv'
        df.to_csv(file_name, index=False)

        time.sleep(5)  # Optional delay before closing

        context.close()
        browser.close()


# washingtonpost_data('gunna', 2012)
# washingtonpost_data('yfn_lucci', 2012)
# washingtonpost_data('young thug', 2012)
# washingtonpost_data('ysl rico', 2012)
# washingtonpost_data('ysl', 2012)

def article_scrape(df_links,
                   element,
                   filename,
                   headless_state=False,
                   script_state=False,
                   sleep_time=0.5):
    """
    Scrape articles from a list of links using Playwright.

    Parameters:
        df_links (list): List of URLs to scrape.
        element (str): CSS selector for the article body.
        filename (str): Name of the output CSV file (without extension).
        headless_state (bool): Whether to run the browser in headless mode.
        script_state (bool): Enable or disable JavaScript execution.
        sleep_time (float): Time to wait between requests in seconds.

    Returns:
        pd.DataFrame: DataFrame containing scraped articles and their corresponding links.
    """
    with sync_playwright() as p:
        # Launch browser and create context
        browser = p.chromium.launch(headless=headless_state)
        context = browser.new_context(java_script_enabled=script_state)
        page = context.new_page()

        # Initialize DataFrame with predefined columns
        df_art = pd.DataFrame(columns=['article', 'links'])

        for link in df_links:
            time.sleep(sleep_time)
            try:
                # Navigate to the link
                page.goto(link, timeout=30000)  # Adjust timeout as needed
                page.wait_for_selector(element, timeout=10000)  # Wait for the element
                time.sleep(sleep_time)
                # Extract all matching elements
                article_elements = page.query_selector_all(element)
                articles = [art.text_content().strip() for art in article_elements]

                # Create a DataFrame with one row per article
                df = pd.DataFrame({'article': '\n'.join(articles), 'links': [link]})

                # Concatenate results into the main DataFrame
                df_art = pd.concat([df_art, df], ignore_index=True)

            except Exception as e:
                print(f"Error scraping link: {link}")
                print(f"Exception: {e}")

                # Append a row with None for failed links
                df_failed = pd.DataFrame({'article': [None], 'links': [link]})
                df_art = pd.concat([df_art, df_failed], ignore_index=True)

        # Close browser and context
        context.close()
        browser.close()

        # Save results to CSV
        output_filename = f"{filename}_art.csv"
        df_art.to_csv(output_filename, index=False)

        print(f"Scraping completed. Results saved to {output_filename}")
        beep(sound = 'success')

        return df_art







# article_scrape(gunna_data['link'],
#                filename='washingtonpost_gunna',
#                headless_state = False,
#                script_state = False,
#                sleep_time = 0.5,
#                element = 'div.wpds-c-PJLV.article-body')
#
# article_scrape(yfn_lucci_data['link'],
#                filename='washingtonpost_yfnlucci',
#                headless_state = False,
#                script_state = False,
#                sleep_time = 0.5,
#                element = 'div.wpds-c-PJLV.article-body')
#
# article_scrape(ysl_data['link'],
#                filename='washingtonpost_ysl',
#                headless_state = False,
#                script_state = False,
#                sleep_time = 0.5,
#                element = 'div.wpds-c-PJLV.article-body')
#
# article_scrape(ysl_rico_data['link'],
#                filename='washingtonpost_yslrico',
#                headless_state = False,
#                script_state = False,
#                sleep_time = 0.5,
#                element = 'div.wpds-c-PJLV.article-body')
#
# beep(sound = 4)

# young_thug_data = pd.read_csv('washingtonpost_young thug.csv')
# gunna_data  = pd.read_csv('washingtonpost_gunna.csv')
# yfn_lucci_data = pd.read_csv('washingtonpost_yfn_lucci.csv')
# ysl_data = pd.read_csv('washingtonpost_ysl.csv')
# ysl_rico_data = pd.read_csv('washingtonpost_ysl rico.csv')
# young_thug_art = pd.read_csv('washingtonpost_youngthug_art.csv')
# gunna_art = pd.read_csv('washingtonpost_gunna_art.csv')
# yfn_lucci_art = pd.read_csv('washingtonpost_yfnlucci_art.csv')
# ysl_art = pd.read_csv('washingtonpost_ysl_art.csv')
# yslrico_art = pd.read_csv('washingtonpost_yslrico_art.csv')
#
# pd.merge(young_thug_data, young_thug_art, left_on='link', right_on='links', how = 'left').drop('link', axis=1).to_csv('youngthug_wp.csv', index=False)
# pd.merge(gunna_data, gunna_art, left_on='link', right_on='links', how = 'left').drop('link', axis=1).to_csv('gunna_wp.csv', index=False)
# pd.merge(yfn_lucci_data, yfn_lucci_art, left_on='link', right_on='links', how = 'left').drop('link', axis=1).to_csv('yfnlucci_wp.csv', index=False)
# pd.merge(ysl_data, ysl_art, left_on='link', right_on='links', how = 'left').drop('link', axis=1).to_csv('ysl_wp.csv', index=False)
# pd.merge(ysl_rico_data, yslrico_art, left_on='link', right_on='links', how = 'left').drop('link', axis=1).to_csv('yslrico_wp.csv', index=False)


'''
New York Reader
'''
def new_york_reader_headline(search_term):
    """Scrape headlines, links, snippets, and dates from the New York Post search results."""
    import time
    import pandas as pd
    from playwright.sync_api import sync_playwright

    base_url = 'https://nypost.com/search/'
    search_term = search_term.replace(' ', '+')
    url = base_url + search_term
    nyp_df = pd.DataFrame()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=30000)

        # CSS selectors for elements
        headlines_element = '.story__headline a'
        date_element = '.meta.meta--byline'
        snippets_element = '.story__excerpt.body'

        while True:
            # Initialize lists for storing data
            headlines = []
            snippets = []
            dates = []
            links = []

            # Get the number of headlines on the current page
            n = page.locator(headlines_element).count()

            for i in range(n):
                try:
                    # Extract headline and link
                    headline_element = page.locator(headlines_element).nth(i)
                    headline = headline_element.text_content().strip()
                    link = headline_element.get_attribute('href')

                    # Extract snippet
                    snippet = page.locator(snippets_element).nth(i).text_content().strip()

                    # Extract date
                    date_text = page.locator(date_element).nth(i).inner_text().strip()
                    date = extract_date_from_html(date_text)

                    # Append data to lists
                    headlines.append(headline)
                    snippets.append(snippet)
                    dates.append(date)
                    links.append(link)
                except Exception as e:
                    print(f"Error extracting data for item {i}: {e}")

            # Add data to DataFrame
            df = pd.DataFrame({'headline': headlines, 'snippet': snippets, 'date': dates, 'links': links})
            nyp_df = pd.concat([nyp_df, df], ignore_index=True)

            # Check for "See More Stories" button
            try:
                button = page.locator("text=See More Stories")
                if button.is_visible():
                    button.scroll_into_view_if_needed()
                    button.click()
                    time.sleep(1)  # Wait for more content to load
                else:
                    break  # Exit loop if no more pages
            except Exception as e:
                print(f"No 'See More Stories' button found or error occurred: {e}")
                break

        context.close()
        browser.close()

    return nyp_df


def extract_date_from_html(html_snippet):
    """Extract the date in 'Month Day, Year' format from the HTML snippet."""
    import re
    match = re.search(r'\b\w+ \d{1,2}, \d{4}\b', html_snippet)
    return match.group(0) if match else None


def nyp_article(aricle_link):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(java_script_enabled= False)
        page = context.new_page()
        page.goto(aricle_link, timeout=30000)
        article_selector = "div.single__content.entry-content.m-bottom"
        page.wait_for_selector(article_selector, timeout=1000)

        # Extract the content of the article
        try:
            article_element = page.locator(article_selector)
            article_text = article_element.inner_text()
            return article_text
        except Exception as e:
            print(f"Error extracting article content: {e}")
            return None

        context.close()
        browser.close()

def nyp_scrapper(search_term):
    # Step 1: Get headlines and links
    headline_df = new_york_reader_headline(search_term)
    pd.set_option('display.max_columns', None)
    print(headline_df.head(5))
    articles = []
    n = len(headline_df)
    for i, link in enumerate(headline_df['links']):
        try:
            article_content = nyp_article(link)  # Fetch article content
            articles.append(article_content)  # Append article content to the list
        except Exception as e:
            print(f"Error fetching article for link {link}: {e}")
            articles.append(None)
        print(f'progress: {i +1} scrapped out of {n} completion: {round((i+1)/n*100, 2)}%, link: {link}')
    # Step 3: Add articles as a new column in the DataFrame
    headline_df['article'] = articles
    filename = search_term.replace(' ', '_') + '_nyp.csv'
    headline_df.to_csv(filename, index=False)
    print(headline_df)
    print(f"Scraping completed. Results saved to {filename}")
    beep(sound = 'success')


    return headline_df


# nyp_scrapper('ysl')
# nyp_scrapper('gunna')
# nyp_scrapper('young thug')
# nyp_scrapper('yfn lucci')
#nyp_scrapper('ysl rico')


\

print(anchor)

