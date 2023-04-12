import nltk
import spacy
import pandas as pd
from textblob import TextBlob
from nltk.corpus import stopwords
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary

from api.assets import constants
from api.models.content import Content
from api.models.chat import Chat
from api.models import db

from api.utils.request import bad_response, response
from api.middleware.error_handlers import internal_error_handler

# One Time Donload is required
# nltk.download('stopwords')
# nltk.download('averaged_perceptron_tagger')

nlp = spacy.load('en_core_web_sm')


def get_related_keywords(content, top_n=5):
    doc = nlp(content)
    tokens = [token for token in doc if not token.is_stop and token.is_alpha and token.has_vector]

    similar_words = set()

    for token in tokens:
        similarities = [(other_token, token.similarity(other_token)) for other_token in doc if other_token != token and other_token.has_vector]
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        top_similar_words = [word[0] for word in sorted_similarities[:top_n]]
        similar_words.update(top_similar_words)

    return [str(word) for word in similar_words]


def get_topics(content):
    doc = nlp(content)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    dictionary = Dictionary([tokens])
    corpus = [dictionary.doc2bow([token]) for token in tokens]
    lda_model = LdaModel(corpus, num_topics=3, id2word=dictionary)
    topics = []
    for topic in lda_model.show_topics():
        words = []
        for word, prob in lda_model.show_topic(topic[0]):
            words.append(word)
        topics.append({'Topic': topic[0], 'Words': words})
    return topics


def get_sentiment(content):
    doc = nlp(content)
    sentences = [sent.text.strip() for sent in doc.sents]  # Change this line
    polarity = 0
    subjectivity = 0
    for sentence in sentences:
        blob = TextBlob(sentence)
        polarity += blob.sentiment.polarity
        subjectivity += blob.sentiment.subjectivity
    avg_polarity = polarity / len(sentences)
    avg_subjectivity = subjectivity / len(sentences)
    if avg_polarity > 0:
        sentiment = 'Positive'
    elif avg_polarity < 0:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    return {'Sentiment': sentiment, 'Polarity': avg_polarity, 'Subjectivity': avg_subjectivity}


def generate_content_ner(content):
    doc = nlp(content)
    entities = []

    for ent in doc.ents:
        entities.append((ent.text, ent.label_))
    
    df = pd.DataFrame(entities, columns=['Entity', 'Label'])
    return df


def get_keywords_and_themes(content):
    doc = nlp(content)
    nouns = []
    adjectives = []
    verbs = []
    
    for token in doc:
        if token.pos_ == 'NOUN' and not token.is_stop:
            nouns.append(token.text)
        elif token.pos_ == 'ADJ' and not token.is_stop:
            adjectives.append(token.text)
        elif token.pos_ == 'VERB' and not token.is_stop:
            verbs.append(token.text)
    
    freq_dist_nouns = nltk.FreqDist(nouns)
    freq_dist_adjectives = nltk.FreqDist(adjectives)
    freq_dist_verbs = nltk.FreqDist(verbs)
    keywords = freq_dist_nouns.most_common(5)

    themes = {
        'Adjectives': freq_dist_adjectives.most_common(2),
        'Verbs': freq_dist_verbs.most_common(2)
    }

    return {'Keywords': [keyword[0] for keyword in keywords], 'Themes': themes}

def is_post_viral(sentiment, keywords_themes, topics, words_embedding):
    # Define a simple criteria for a viral post
    viral_criteria = {
        'positive_sentiment': True,
        'popular_keywords': 3,
        'distinct_topics': 2,
    }

    # Check if the criteria are met
    is_viral = False
    positive_sentiment = sentiment['Sentiment'] == 'Positive'
    popular_keywords = len(set(keywords_themes['Keywords'])) >= viral_criteria['popular_keywords']
    distinct_topics = len(topics) >= viral_criteria['distinct_topics']

    if positive_sentiment and popular_keywords and distinct_topics:
        is_viral = True

    return is_viral


@internal_error_handler
def linkedin_analysis(user, content):
    named_entity_recognition_df = generate_content_ner(content)
    keywords_themes = get_keywords_and_themes(content)
    sentiment = get_sentiment(content)
    topics = get_topics(content)
    words_embedding = get_related_keywords(content)

    # Determine if the post is viral or not
    viral = is_post_viral(sentiment, keywords_themes, topics, words_embedding)

    # Return the results as a JSON object
    return response(
        success=True, 
        message=constants.SuccessMessage.content_generated, 
        named_entity_recognition=named_entity_recognition_df.to_dict(orient='records'),
        keywords_themes=keywords_themes,
        sentiment=sentiment,
        topics=topics,
        words_embedding=words_embedding,
        viral=viral
    )