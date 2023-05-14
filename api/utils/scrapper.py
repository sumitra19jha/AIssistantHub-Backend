import os
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import time
import re

from config import Config

API_KEY = Config.GOOGLE_SEARCH_API_KEY
CUSTOM_SEARCH_ENGINE_ID = Config.CUSTOM_SEARCH_ENGINE_ID

class AssistantHubScrapper:
    def get_country_code_from_ip(ip_address):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'success':
                return data['countryCode'].lower()
        except Exception as e:
            print(f"Error fetching country code: {e}")
            return None

    def get_country_name_from_ip(ip_address):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'success':
                return data['country'].lower()
        except Exception as e:
            print(f"Error fetching country name: {e}")
            return None

    def get_country_name_and_code_from_ip(ip_address):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'success':
                return data['country'].lower(), data['countryCode'].lower()
            else:
                return None, None
        except Exception as e:
            print(f"Error fetching country name: {e}")
            return None, None

    def fetch_url_content(url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        
        # Extract text from the webpage
        text = soup.get_text(strip=True)

        # Extract additional information, such as titles and summaries
        title = None
        summary = None

        # Look for the title in common HTML elements
        title_element = soup.find('title') or soup.find('h1') or soup.find('h2')
        if title_element:
            title = title_element.get_text(strip=True)

        # Look for a summary in common HTML elements
        summary_element = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
        if summary_element:
            summary = summary_element['content']
        else:
            summary = ''

        return {
            'text': text,
            'title': title,
            'summary': summary
        }
        
    def preprocess_content(content):
        text = content['text']
        title = content['title']
        summary = content['summary']

        if isinstance(text, str):
            text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
            text = text.strip()  # Remove leading and trailing spaces

        if isinstance(title, str):
            title = re.sub(r'\s+', ' ', title)  # Remove extra whitespace
            title = title.strip()  # Remove leading and trailing spaces

        if isinstance(summary, str):
            summary = re.sub(r'\s+', ' ', summary)  # Remove extra whitespace
            summary = summary.strip()  # Remove leading and trailing spaces

        return {
            'text': text,
            'title': title,
            'summary': summary
        }

    def tokenize_content(content):
        text = content['text'].split()
        title = content['title'].split()
        summary = content['summary'].split()

        combined_tokens = text + title + summary

        return combined_tokens
    
    def google_search(query, user_location=None):
        service = build("customsearch", "v1", developerKey=API_KEY)
        search_params = {'q': query, 'cx': CUSTOM_SEARCH_ENGINE_ID}

        if user_location:
            search_params['gl'] = user_location.upper()
        
        results = service.cse().list(**search_params).execute()
        return results.get('items', [])

    def search_and_crawl(query, user_ip, max_total_tokens=1000):
        total_point = 0.0
        country_code = AssistantHubScrapper.get_country_code_from_ip(user_ip)
        
        if not country_code:
            country_code = 'IN'
        
        search_results = AssistantHubScrapper.google_search(query, country_code)
        total_point += 0.0005

        all_contents = []
        total_tokens = 0
        
        for result in search_results:
            if total_tokens >= max_total_tokens:
                break

            url = result['link']
            website = result['displayLink']
            content = AssistantHubScrapper.fetch_url_content(url)

            if content:
                preprocessed_content = AssistantHubScrapper.preprocess_content(content)
                tokens = AssistantHubScrapper.tokenize_content(preprocessed_content)
                remaining_tokens = max_total_tokens - total_tokens

                truncated_tokens = tokens[:remaining_tokens]
                truncated_content = ' '.join(truncated_tokens)
                total_tokens += len(truncated_tokens)

                content_map = {
                    'website': website,
                    'content': truncated_content
                }

                all_contents.append(content_map)
                time.sleep(1)  # Respect the website's rate limits

        return all_contents, total_point