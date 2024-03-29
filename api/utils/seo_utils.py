from sklearn.metrics.pairwise import cosine_similarity
from gensim import corpora, models, similarities
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

import re
import datetime
from isodate import parse_duration
import nltk
import praw
import requests

import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import Counter
from api.models.search_query import SearchQuery
from api.assets import constants
from api.utils.db import add_commit_
from config import Config
from api.utils import logging_wrapper
import nltk

# Download the NLTK stop words and tokenize resources
nltk.download("stopwords")
nltk.download("punkt")

reddit = praw.Reddit(
    client_id=Config.REDDIT_CLIENT_ID,
    client_secret=Config.REDDIT_CLIENT_SECRET,
    user_agent=Config.REDDIT_USER_AGENT,
)

logger = logging_wrapper.Logger(__name__)

class AssistantHubSEO:
    # Uses Google Search Engine and search based on user Input
    # The current form of Query is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def fetch_google_search_results(query, num_pages=1):
        search_articles = []

        for i in range(num_pages):
            start = i * 10 + 1
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": Config.GOOGLE_SEARCH_API_KEY,
                "cx": Config.CUSTOM_SEARCH_ENGINE_ID,
                "q": query,
                "start": start,
                'sort': 'date',  # Sort results by recency
                'lr': 'lang_en',  # Fetch articles in English
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                results = response.json()
                search_article_items = results.get('items', [])
                search_articles.extend(search_article_items)
            else:
                logger.exception(f"Error: {response.status_code}")
                print(f"Error: {response.status_code}")
                continue
        return search_articles

    def analyze_google_search_results(search_results):
        # Initialize the stop words and stemmer
        stop_words = set(stopwords.words("english"))
        stemmer = PorterStemmer()

        # Extract the titles, snippets, and URLs from the search results
        text_data = []
        for item in search_results.get("items", []):
            text_data.append(item.get("title", ""))
            text_data.append(item.get("snippet", ""))
            text_data.append(item.get("link", ""))

        # Tokenize the text data
        tokens = nltk.word_tokenize(" ".join(text_data).lower())

        # Filter out stop words and non-alphabetic tokens
        filtered_tokens = [
            token for token in tokens if token.isalpha() and token not in stop_words]

        # Perform stemming on the filtered tokens
        stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]

        # Calculate the frequency of the stemmed tokens
        token_freq = Counter(stemmed_tokens)

        # Return the most common keywords and their frequencies
        return token_freq.most_common()

    def analyze_competion_page(html):
        soup = BeautifulSoup(html, "html.parser")

        # Title tags, Meta Description and Header Tags
        title = soup.title.string if soup.title else None
        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description["content"] if meta_description else None
        header_tags = [tag.text for tag in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"])]

        # Keyword density
        text = " ".join([tag.text for tag in soup.find_all("p")])
        tokens = nltk.word_tokenize(text.lower())
        filtered_tokens = [token for token in tokens if token.isalnum()]
        keyword_density = Counter(filtered_tokens)

        # Internal/external links
        links = soup.find_all("a")
        domain = urlparse(html).netloc
        internal_links = []
        external_links = []

        for link in links:
            href = link.get("href")
            if not href:
                continue
            if href.startswith("http") and domain not in href:
                external_links.append({"url": href, "anchor_text": link.text})
            else:
                internal_links.append({"url": href, "anchor_text": link.text})

        return {
            "title": title,
            "meta_description": meta_description,
            "header_tags": header_tags,
            "keyword_density": keyword_density,
            "internal_links": internal_links,
            "external_links": external_links,
        }

    def process_post(post):
        post_title = post.title
        post_body = post.selftext
        post.comments.replace_more(limit=0)  # Limit to top-level comments only
        post_comments = [comment.body for comment in post.comments.list()]
        return post_title, post_body, post_comments

    def analyze_text(text):
        stop_words = set(stopwords.words("english"))
        stemmer = PorterStemmer()
        tokens = nltk.word_tokenize(text.lower())
        filtered_tokens = [
            token for token in tokens if token.isalpha() and token not in stop_words]
        stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]
        token_freq = Counter(stemmed_tokens)
        return token_freq.most_common()

    def analyze_reddit_subreddit(subreddit_name, post_limit=10):
        subreddit = reddit.subreddit(subreddit_name)
        top_posts = subreddit.top(limit=post_limit)
        all_post_titles = []
        all_post_bodies = []
        all_comments = []
        posts = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            post_results = executor.map(
                AssistantHubSEO.process_post, top_posts)
            for post_title, post_body, post_comments in post_results:
                all_post_titles.append(post_title)
                all_post_bodies.append(post_body)
                all_comments.extend(post_comments)
                posts.append({
                    "title": post_title,
                    "body": post_body,
                    "comments": post_comments,
                })

        title_keywords = AssistantHubSEO.analyze_text(
            " ".join(all_post_titles))
        body_keywords = AssistantHubSEO.analyze_text(" ".join(all_post_bodies))
        comment_keywords = AssistantHubSEO.analyze_text(" ".join(all_comments))

        return {
            "title_keywords": title_keywords,
            "body_keywords": body_keywords,
            "comment_keywords": comment_keywords,
            "posts": posts,
        }

    def get_lsi_topic_and_keywords(texts, num_topics=5, num_words=10):
        # Tokenize and preprocess the text data
        texts = [nltk.word_tokenize(text.lower()) for text in texts]
        texts = [[token for token in text if token.isalpha()]
                 for text in texts]

        # Create a dictionary from the tokenized texts
        dictionary = corpora.Dictionary(texts)

        # Convert the tokenized texts into a bag of words representation
        corpus = [dictionary.doc2bow(text) for text in texts]

        # Train the LSI model and extract the topics
        lsi_model = models.LsiModel(
            corpus, num_topics=num_topics, id2word=dictionary)
        topics = lsi_model.show_topics(
            num_topics=num_topics, num_words=num_words)

        # Extract the top keywords from each topic
        keywords = []
        for topic in topics:
            top_words = [word.split("*")[1].strip()
                         for word in topic[1].split("+")]
            keywords.extend(top_words)

        return {
            "topics": topics,
            "keywords": keywords,
        }

    def get_long_tail_keywords(texts, max_keywords=50, n_components=100):
        # Tokenize and preprocess the text data
        texts = [nltk.word_tokenize(text.lower()) for text in texts]
        texts = [[token for token in text if token.isalpha()]
                 for text in texts]

        # Calculate the TF-IDF matrix
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(
            [" ".join(text) for text in texts])

        # Reduce the dimensionality of the matrix using truncated SVD
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        tfidf_matrix_svd = svd.fit_transform(tfidf_matrix)

        # Calculate the cosine similarities between all pairs of documents
        similarities = cosine_similarity(tfidf_matrix_svd)

        # Get the top keywords for each document
        top_keywords = []
        for i, text in enumerate(texts):
            keywords = [word for _, word in sorted(
                zip(similarities[i], text), reverse=True)]
            top_keywords.append(keywords[:max_keywords])

        # Count the frequency of each keyword and return the top keywords
        all_keywords = [
            keyword for keywords in top_keywords for keyword in keywords]
        keyword_freq = Counter(all_keywords)
        return keyword_freq.most_common(max_keywords)

    def fetch_html(url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None
