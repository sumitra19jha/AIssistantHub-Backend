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
    def fetch_url_content(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        
    def preprocess_content(content):
        content = re.sub(r'\s+', ' ', content)  # Remove extra whitespace
        content = content.strip()  # Remove leading and trailing spaces
        return content

    def tokenize_content(content):
        return content.split()
    
    def google_search(query):
        service = build("customsearch", "v1", developerKey=API_KEY)
        results = service.cse().list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID).execute()
        return results.get('items', [])

    def search_and_crawl(query, max_total_tokens=2000):
        search_results = AssistantHubScrapper.google_search(query)

        all_contents = []
        total_tokens = 0
        for result in search_results:
            if total_tokens >= max_total_tokens:
                break

            url = result['link']
            if "twitter" in  url:
                continue
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

        return all_contents