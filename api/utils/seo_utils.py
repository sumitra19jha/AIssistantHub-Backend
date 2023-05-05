import gensim
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
from pytrends.request import TrendReq
from googleplaces import GooglePlaces
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from api.utils.db import add_commit_, add_flush_

from config import Config

import nltk
from nltk.tokenize import word_tokenize
from gensim.models import TfidfModel
from gensim.corpora import Dictionary

from api.models.youtube_video_analysis import YouTubeVideoAnalysis
from api.models.youtube_search_query import YouTubeSearchQuery
from api.models.youtube_search_video_rel import YouTubeSearchVideoRel

# Download the NLTK stop words and tokenize resources
nltk.download("stopwords")
nltk.download("punkt")

reddit = praw.Reddit(
    client_id=Config.REDDIT_CLIENT_ID,
    client_secret=Config.REDDIT_CLIENT_SECRET,
    user_agent=Config.REDDIT_USER_AGENT,
)


class AssistantHubSEO:
    def is_relevant_keyword(keyword):
        # Remove keywords containing only numbers, ".", "http", or "https"
        if re.match(r"^\d+$|^\.+$|^http$|^https$", keyword):
            return False

        # Remove keywords containing URLs
        if re.search(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", keyword):
            return False

        # TODO: Add more filtering conditions if needed

        return True

    def filter_keywords(ranked_keywords):
        filtered_keywords = [kw for kw, score in ranked_keywords if AssistantHubSEO.is_relevant_keyword(kw)]
        return filtered_keywords

    def calculate_video_score(video):
        score = 0

        # Assign weights for each factor
        weight_views = 2
        weight_likes = 1.5
        weight_comments = 1
        weight_duration = 0.5

        # Normalize the factors
        normalized_views = video.views / (video.views + 2)
        normalized_likes = video.likes_count / (video.likes_count + 2)
        normalized_comments = video.comments_count / (video.comments_count + 2)
        normalized_duration = video.video_duration / (video.video_duration + 2)

        # Calculate the score
        score = (
            weight_views * normalized_views +
            weight_likes * normalized_likes +
            weight_comments * normalized_comments +
            weight_duration * normalized_duration
        )

        return score
    
    def calculate_keyword_score(top_keywords, video_data):
        keyword_scores = {}

        for i, video_keywords in enumerate(top_keywords):
            video = video_data[i]
            video_score = AssistantHubSEO.calculate_video_score(video)

            for keyword, tfidf_value in video_keywords:
                if keyword not in keyword_scores:
                    keyword_scores[keyword] = 0
                
                keyword_scores[keyword] += tfidf_value * video_score

        return keyword_scores

    def rank_keywords(keyword_scores):
        ranked_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked_keywords
    
    def preprocess_text(text):
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [token.lower() for token in tokens if token.isalnum() and token.lower() not in stop_words]
        return filtered_tokens

    def yotube_video_keywords_extraction(video_data):
        title_documents = []
        description_documents = []

        for video in video_data:
            title_tokens = AssistantHubSEO.preprocess_text(video.title)
            description_tokens = AssistantHubSEO.preprocess_text(video.description)
            title_documents.append(title_tokens)
            description_documents.append(description_tokens)

        return title_documents, description_documents

    def compute_tfidf_matrix(documents):
        dictionary = Dictionary(documents)
        corpus = [dictionary.doc2bow(doc) for doc in documents]
        tfidf_model = TfidfModel(corpus)
        return tfidf_model, corpus, dictionary

    def identify_top_keywords(tfidf_model, corpus, dictionary, top_n=10):
        top_keywords = []

        for doc in corpus:
            doc_tfidf = tfidf_model[doc]
            sorted_tfidf = sorted(doc_tfidf, key=lambda x: x[1], reverse=True)
            top_terms = [(dictionary[term_id], tfidf_value) for term_id, tfidf_value in sorted_tfidf[:top_n]]
            top_keywords.append(top_terms)

        return top_keywords
    
    # Uses Google Search Engine and search based on user Input
    # The current form of Query is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def fetch_google_search_results(query, num_pages=1):
        results = []
        for i in range(num_pages):
            start = i * 10 + 1
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": Config.GOOGLE_SEARCH_API_KEY,
                "cx": Config.CUSTOM_SEARCH_ENGINE_ID,
                "q": query,
                "start": start
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                results.extend(response.json()["items"])
            else:
                print(f"Error: {response.status_code}")
                break
        return {"items": results}

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

    # Uses Youtube V3 API for search based on user Input
    # The current form of Query for Search is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def youtube_search(query_arr, seo_id, max_results=5):
        youtube = build('youtube', 'v3', developerKey=Config.GOOGLE_YOUTUBE_1_API_KEY)

        video_response = []
        video_ids = []

        # Calculate date one year ago from today
        one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')

        for query in query_arr:
            try:
                search_model = YouTubeSearchQuery.query.filter_by(
                    search_query=query,
                    youtube_seo_analysis_id=seo_id
                ).first()

                if search_model is None:
                    search_model = YouTubeSearchQuery(
                        search_query=query,
                        youtube_seo_analysis_id=seo_id,
                    )
                    add_commit_(search_model)

                search_response = youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=max_results,
                    type='video',
                    videoDefinition='high',
                    order='viewCount',
                    publishedAfter=one_year_ago
                ).execute()

                for search_result in search_response.get("items", []):
                    if search_result["id"]["kind"] == "youtube#video":
                        video_id = search_result["id"]["videoId"]
                        if video_id in video_ids:
                            continue

                        video_info = youtube.videos().list(
                            part="snippet,statistics,contentDetails",
                            id=video_id
                        ).execute()["items"][0]

                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        thumbnail_url = search_result["snippet"]["thumbnails"]["default"]["url"]
                        video_duration = parse_duration(video_info["contentDetails"]["duration"]).total_seconds()

                        video_model = YouTubeVideoAnalysis.query.filter_by(video_id=video_id).first()

                        if video_model is None:
                            video_model = YouTubeVideoAnalysis(
                                video_id=video_id,
                                video_url=video_url,
                                thumbnail_url=thumbnail_url,
                                video_duration=video_duration,
                                title=search_result["snippet"]["title"],
                                description=video_info["snippet"]["description"],
                                channel_title=search_result["snippet"]["channelTitle"],
                                publish_date=video_info["snippet"]["publishedAt"],
                                views=int(video_info["statistics"].get("viewCount", "-1")),
                                likes_count=int(video_info["statistics"].get("likeCount", "-1")),
                                comments_count=int(video_info["statistics"].get("commentCount", "-1"))
                            )
                            add_commit_(video_model)

                        video_response.append(video_model)

                        search_video_rel_model = YouTubeSearchVideoRel.query.filter_by(
                            youtube_search_query_id=search_model.id,
                            youtube_video_analysis_id=video_model.id
                        ).first()

                        if search_video_rel_model is None:
                            search_video_rel_model = YouTubeSearchVideoRel(
                                youtube_search_query_id=search_model.id,
                                youtube_video_analysis_id=video_model.id,
                            )
                            add_commit_(search_video_rel_model)

                        video_ids.append(video_id)

            except HttpError as e:
                videos_without_stats = AssistantHubSEO.youtube_search_without_statistics(query_arr, max_results)
                return videos_without_stats

        return video_response


    def youtube_search_without_statistics(query_arr, max_results=5):
        youtube = build('youtube', 'v3', developerKey=Config.GOOGLE_SEARCH_API_KEY)
        videos = []

        # Calculate date one year ago from today
        one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')

        for query in query_arr:
            try:
                search_response = youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=max_results,
                    type='video',
                    videoDefinition='high',
                    order='viewCount',
                    publishedAfter=one_year_ago
                ).execute()

                for search_result in search_response.get("items", []):
                    if search_result["id"]["kind"] == "youtube#video":
                        video_id = search_result["id"]["videoId"]
                        
                        video_info = youtube.videos().list(
                            part="snippet,contentDetails",
                            id=video_id
                        ).execute()["items"][0]

                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        thumbnail_url = search_result["snippet"]["thumbnails"]["default"]["url"]
                        video_duration = parse_duration(video_info["contentDetails"]["duration"]).total_seconds()

                        videos.append(
                            {
                                "title": search_result["snippet"]["title"],
                                "description": video_info["snippet"]["description"],
                                "video_id": video_id,
                                "video_url": video_url,
                                "channel_title": search_result["snippet"]["channelTitle"],
                                "publish_date": video_info["snippet"]["publishedAt"],
                                "thumbnail_url": thumbnail_url,
                                "views": 0,
                                "likes_count": 0,
                                "comments_count": 0,
                                "video_duration": video_duration
                            }
                        )
            except HttpError as e:
                print(f"An error occurred: {e}")
                videos_without_statistics_content = AssistantHubSEO.youtube_search_without_statistics_without_duration(query_arr, max_results)
                return videos_without_statistics_content

        return videos

    def youtube_search_without_statistics_without_duration(query_arr, max_results=5):
        youtube = build('youtube', 'v3', developerKey=Config.GOOGLE_SEARCH_API_KEY)
        videos = []

        # Calculate date one year ago from today
        one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')

        for query in query_arr:
            try:
                search_response = youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=max_results,
                    type='video',
                    videoDefinition='high',
                    order='viewCount',
                    publishedAfter=one_year_ago
                ).execute()

                for search_result in search_response.get("items", []):
                    if search_result["id"]["kind"] == "youtube#video":
                        video_id = search_result["id"]["videoId"]
                        
                        video_info = youtube.videos().list(
                            part="snippet",
                            id=video_id
                        ).execute()["items"][0]

                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        thumbnail_url = search_result["snippet"]["thumbnails"]["default"]["url"]
                        video_duration = 0

                        videos.append(
                            {
                                "title": search_result["snippet"]["title"],
                                "description": video_info["snippet"]["description"],
                                "video_id": video_id,
                                "video_url": video_url,
                                "channel_title": search_result["snippet"]["channelTitle"],
                                "publish_date": video_info["snippet"]["publishedAt"],
                                "thumbnail_url": thumbnail_url,
                                "views": 0,
                                "likes_count": 0,
                                "comments_count": 0,
                                "video_duration": video_duration
                            }
                        )
            except HttpError as e:
                print(f"An error occurred: {e}")
                return []

        return videos

    # Uses Google News API for search based on user Input
    # The current form of Query for Search is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def fetch_google_news(query):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": Config.GOOGLE_SEARCH_API_KEY,
            "cx": Config.CUSTOM_SEARCH_ENGINE_ID,
            "q": query,
            "tbm": "nws"
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None

    # Uses Google Places API for search based on user Input
    # The current form of Query for Search is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def fetch_google_places(query):
        google_places = GooglePlaces(Config.GOOGLE_SEARCH_API_KEY_FOR_PLACES)
        query_result = google_places.text_search(query=query)

        places_data = []
        for place in query_result.places:
            place.get_details()
            place_dict = {
                "name": place.name,
                "address": place.formatted_address,
                "google_maps_url": f"https://maps.google.com/?q={place.geo_location['lat']},{place.geo_location['lng']}",
                "latitude": place.geo_location["lat"],
                "longitude": place.geo_location["lng"]
            }
            if hasattr(place, 'website'):
                place_dict["website"] = place.website
            if hasattr(place, 'rating'):
                place_dict["rating"] = place.rating
            places_data.append(place_dict)

        return places_data

    def fetch_competitors(query):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": Config.GOOGLE_SEARCH_API_KEY,
            "cx": Config.CUSTOM_SEARCH_ENGINE_ID,
            "q": query
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return [item["link"] for item in response.json().get("items", [])]
        else:
            print(f"Error: {response.status_code}")
            return []

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
