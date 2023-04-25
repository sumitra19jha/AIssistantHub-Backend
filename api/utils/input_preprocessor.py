import re
import requests
from bs4 import BeautifulSoup

from api.utils.dashboard import DashboardUtils

class InputPreprocessor:
    def preprocess_user_input(topic, urls, length):
        topic = topic.strip()
        if len(topic) == 0:
            raise ValueError("Topic cannot be empty.")

        parsed_urls = []
        for url in urls:
            # Remove leading and trailing whitespace
            url_type = url["type"].upper().strip()
            clean_url = url["url"].strip()

            # Check if the URL is valid
            if not re.match(r'https?://\S+', clean_url):
                raise ValueError("Invalid URL.")

            if url_type not in ['RESEARCH', 'COMPETITION']:
                raise ValueError(
                    "Invalid URL type. Accepted types are Research and Competition.")

            parsed_url_data = {
                "url": clean_url,
                "type": url_type,
            }

            parsed_urls.append(parsed_url_data)

        url_contents = []
        for url in parsed_urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raise an exception for HTTP errors
                soup = BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                # Handle request errors, such as timeouts, DNS resolution errors, or invalid URLs
                print(f"Error fetching URL: {url} - {e}")
                continue

            # Extract text from the webpage
            text = soup.get_text(strip=True)

            # Extract additional information, such as titles and summaries
            title = None
            summary = None

            # Look for the title in common HTML elements
            title_element = soup.find('title') or soup.find(
                'h1') or soup.find('h2')
            if title_element:
                title = title_element.get_text(strip=True)

            # Look for a summary in common HTML elements
            summary_element = soup.find('meta', attrs={'name': 'description'}) or \
                soup.find('meta', attrs={'property': 'og:description'})
            if summary_element:
                summary = summary_element['content']

            url_info = {
                'text': text,
                'title': title,
                'summary': summary
            }

            url_contents.append(url_info)

        content_length = DashboardUtils.sizeOfContent(type, length)
        
        return {
            'topic': topic,
            'urls': parsed_urls,
            'length': content_length,
            'url_contents': url_contents
        }


    def preprocess_user_input_for_social_media_post(topic, urls, length, platform):
        platform = platform.upper().strip()

        if platform not in ['LINKEDIN', 'TWITTER', 'FACEBOOK', 'INSTAGRAM']:
            raise ValueError(
                "Invalid platform. Accepted platforms are LinkedIn, Twitter, Facebook, and Instagram.",
            )

        topic = topic.strip()
        if len(topic) == 0:
            raise ValueError("Topic cannot be empty.")

        parsed_urls = []
        for url in urls:
            # Remove leading and trailing whitespace
            url_type = url["type"].upper().strip()
            clean_url = url["url"].strip()

            # Check if the URL is valid
            if not re.match(r'https?://\S+', clean_url):
                raise ValueError("Invalid URL.")

            if url_type not in ['RESEARCH', 'COMPETITION']:
                raise ValueError(
                    "Invalid URL type. Accepted types are Research and Competition.")

            parsed_url_data = {
                "url": clean_url,
                "type": url_type,
            }

            parsed_urls.append(parsed_url_data)

        url_contents = []
        for url in parsed_urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raise an exception for HTTP errors
                soup = BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                # Handle request errors, such as timeouts, DNS resolution errors, or invalid URLs
                print(f"Error fetching URL: {url} - {e}")
                continue

            # Extract text from the webpage
            text = soup.get_text(strip=True)

            # Extract additional information, such as titles and summaries
            title = None
            summary = None

            # Look for the title in common HTML elements
            title_element = soup.find('title') or soup.find(
                'h1') or soup.find('h2')
            if title_element:
                title = title_element.get_text(strip=True)

            # Look for a summary in common HTML elements
            summary_element = soup.find('meta', attrs={'name': 'description'}) or \
                soup.find('meta', attrs={'property': 'og:description'})
            if summary_element:
                summary = summary_element['content']

            url_info = {
                'text': text,
                'title': title,
                'summary': summary
            }

            url_contents.append(url_info)

        content_length = DashboardUtils.sizeOfContent(type, length)
        return {
            'platform': platform,
            'topic': topic,
            'urls': parsed_urls,
            'length': content_length,
            'url_contents': url_contents
        }