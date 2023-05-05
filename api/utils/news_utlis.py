import re
import json
import requests

import nltk
import openai

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from gensim.models import TfidfModel, LdaModel
from gensim.corpora import Dictionary
from gensim.matutils import corpus2dense
from collections import Counter
from sklearn.cluster import KMeans
from gensim.models.coherencemodel import CoherenceModel
from api.models.news_analysis import NewsAnalysis
from api.models.news_search_rel import NewsSearchRel
from api.models.search_query import SearchQuery

from api.assets import constants
from api.utils import logging_wrapper
from api.utils.db import add_commit_
from config import Config

logger = logging_wrapper.Logger(__name__)

class AssistantHubNewsAlgo:
    def clean_title(title):
        # Remove characters like "\", "/", and quotes
        cleaned_title = re.sub(r'[\\\/"]', '', title)

        # Remove extra spaces
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()

        return cleaned_title

    # Preprocessing function
    def preprocess(text):
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
        text = text.lower()  # Convert text to lowercase
        tokens = nltk.word_tokenize(text)  # Tokenize words
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stopwords.words('english')]
        return tokens

    # Build a dictionary and a corpus for the articles
    def keywords_titles_builder(news_data):
        # Preprocess the articles
        articles = [article["snippet"] for article in news_data]
        preprocessed_articles = [AssistantHubNewsAlgo.preprocess(article) for article in articles]

        # Build a dictionary and a corpus for the articles
        dictionary = Dictionary(preprocessed_articles)
        corpus = [dictionary.doc2bow(article) for article in preprocessed_articles]

        # Calculate TF-IDF scores
        tfidf_model = TfidfModel(corpus)
        tfidf_corpus = tfidf_model[corpus]

        # Convert the tfidf_corpus to a dense matrix
        dense_tfidf_corpus = corpus2dense(tfidf_corpus, num_terms=len(dictionary)).T


        # Extract top keywords and key phrases
        top_keywords = Counter()
        for doc in tfidf_corpus:
            top_keywords.update({dictionary[word_id]: score for word_id, score in doc})

        # Topic modeling using LDA
        lda_model = LdaModel(corpus, num_topics=5, id2word=dictionary, passes=20)
        
        # Compute the topic coherence score
        coherence_model_lda = CoherenceModel(model=lda_model, texts=preprocessed_articles, dictionary=dictionary, coherence='c_v')
        coherence_lda = coherence_model_lda.get_coherence()

        # Filter out irrelevant topics based on a minimum threshold (e.g., 0.3)
        min_coherence_threshold = 0.3
        if coherence_lda >= min_coherence_threshold:
            topics = lda_model.show_topics(num_topics=5, num_words=5, formatted=False)
        else:
            # Handle the case where the topics are not coherent enough
            print("The topics are not coherent enough. Please try again later.")

        # Clustering using KMeans
        kmeans = KMeans(n_clusters=5)
        clusters = kmeans.fit_predict(dense_tfidf_corpus)

        # Analyzing trends and events
        trending_topics = []
        for cluster in range(5):
            cluster_articles = [article for article, c in zip(articles, clusters) if c == cluster]
            cluster_keywords = Counter()
            for article in cluster_articles:
                article_keywords = AssistantHubNewsAlgo.preprocess(article)
                cluster_keywords.update(article_keywords)
            trending_topics.append(cluster_keywords.most_common(5))

        return trending_topics

    # Generating content titles
    def generate_title(keywords, user):
        # Join the top keywords with a comma
        keywords_str = ", ".join([keyword[0] for keyword in keywords])

        system_prompt = {
            "role": "system",
            "content": "You are an AI assistant trained to generate relevant and engaging article titles based on a set of keywords. Generate a title using the following keywords."
        }

        user_prompt = {
            "role": "user",
            "content": f"Keywords: {keywords_str}"
        }

        assistant_response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL_GPT4,
            messages=[system_prompt, user_prompt],
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            user=str(user.id),
        )

        # Extract and format the title
        title = assistant_response["choices"][0]["message"]["content"].strip()
        return title

    # Fetch News search text
    def generate_news_search_text_gpt4(user, business_type, target_audience, industry, location):
        try:
            system_prompt = {
                "role": "system",
                "content": "You are a News Search Query Writer AI assistant. Your primary work is to write search queries on google based on user input that provides relevant results which will be helpful for users.\n\nYour response should be pointwise."
            }

            user_prompt = {
                "role": "user",
                "content": f"User Input\n```\nBusiness type: {business_type}\nTarget audience: {target_audience}\nIndustry: {industry}\nLocation: {location}\n```"
            }

            assistant_response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL_GPT4,
                messages=[system_prompt, user_prompt],
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                user=str(user.id),
            )

            # Extract and format search queries as an array
            search_queries = assistant_response["choices"][0]["message"]["content"].strip().split("\n")
            return search_queries
        except Exception as e:
            logger.exception(str(e))
            return None

    # Uses Google News API for search based on user Input
    # The current form of Query for Search is:
    #   "{business_type} {target_audience} {industry} {goals}"
    def fetch_google_news(query_arr, project_id, num_results=5):
        news_articles = []
        base_url = 'https://www.googleapis.com/customsearch/v1'

        for query in query_arr:
            search_model = SearchQuery.query.filter(
                SearchQuery.search_query == query,
                SearchQuery.seo_project_id == project_id,
                SearchQuery.type == constants.ProjectTypeCons.enum_news,
            ).first()

            if search_model is None:
                search_model = SearchQuery(
                    search_query=query,
                    seo_project_id=project_id,
                    type=constants.ProjectTypeCons.enum_news,
                )
                add_commit_(search_model)

            params = {
                'q': f"{query} AND when:7d",  # Fetch articles from the past 7 days
                'cx': Config.CUSTOM_SEARCH_ENGINE_ID,
                'key': Config.GOOGLE_SEARCH_API_KEY,
                'num': num_results,
                'sort': 'date',  # Sort results by recency
                'lr': 'lang_en',  # Fetch articles in English
                'tbm': 'nws',  # Filter results to news articles only
            }

            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                results = response.json()
                news_article_items = results.get('items', [])
                news_articles.extend(news_article_items)

                for news_article_map in news_article_items:
                    model_article = NewsAnalysis.query.filter(NewsAnalysis.link == news_article_map["link"]).first()

                    if model_article is None:
                        model_article = NewsAnalysis(
                            title=news_article_map["htmlTitle"],
                            display_link=news_article_map["displayLink"],
                            formatted_url=news_article_map["formattedUrl"],
                            snippet=news_article_map["htmlSnippet"],
                            kind=news_article_map["kind"],
                            link=news_article_map["link"],
                            pagemap=news_article_map["pagemap"],
                        )

                        add_commit_(model_article)

                    search_news_rel_model = NewsSearchRel.query.filter(
                        NewsSearchRel.search_query_id == search_model.id,
                        NewsSearchRel.news_analysis_id == model_article.id
                    ).first()

                    if search_news_rel_model is None:
                        search_news_rel_model = NewsSearchRel(
                            search_query_id=search_model.id,
                            news_analysis_id=model_article.id
                        )
                        add_commit_(search_news_rel_model)
            else:
                logger.exception(f"Error: {response.status_code}")
                print(f"Error: {response.status_code}")
                return None

        return news_articles
