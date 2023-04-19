import nltk
import spacy
import openai
import textstat
import language_tool_python
from typing import List

import gensim
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
import gensim.corpora as corpora
from gensim.models import CoherenceModel
from nltk.stem import WordNetLemmatizer
from scipy.spatial.distance import cosine

from config import Config
from api.assets import constants
from api.utils.request import response
from api.models.content import Content
from api.middleware.error_handlers import internal_error_handler


nltk.download('wordnet')


openai.api_key = Config.OPENAI_API_KEY
nlp = spacy.load("en_core_web_md")
tool = language_tool_python.LanguageTool("en-US");
embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")


def best_content(prompt: str, generated_contents: List[str]) -> str:
    scores = []
    for content in generated_contents:
        relevance_score = relevance(prompt, content)
        coherence_score = coherence(content)
        readability_score = readability(content)
        grammar_score = grammar_and_spelling(content)
        length_score = length(content)

        # Assign weights to each metric and calculate the overall score
        total_score = (
            0.4 * relevance_score
            + 0.2 * coherence_score
            + 0.2 * readability_score
            + 0.1 * grammar_score
            + 0.1 * length_score
        )

        scores.append(total_score)

    best_index = scores.index(max(scores))
    return generated_contents[best_index]

# Measure the relevance of User Message with the Update generated
def relevance(prompt: str, content: str) -> float:
    # Generate embeddings for the prompt and the generated content
    embeddings = embed([prompt, content])

    # Calculate the cosine similarity between the embeddings
    similarity = 1 - cosine(embeddings[0], embeddings[1])

    return similarity

def coherence(content: str) -> float:
    # Tokenize and preprocess the content
    tokens = preprocess(content)

    # Create a dictionary representation of the documents
    id2word = corpora.Dictionary([tokens])

    # Create a Bag of Words representation of the content
    corpus = [id2word.doc2bow(text) for text in [tokens]]

    # Create an LDA model using Gensim
    lda_model = gensim.models.LdaMulticore(corpus, num_topics=1, id2word=id2word, passes=2, workers=2)

    # Calculate coherence score using the CoherenceModel from Gensim
    coherence_model_lda = CoherenceModel(model=lda_model, texts=[tokens], dictionary=id2word, coherence='c_v')
    coherence_lda = coherence_model_lda.get_coherence()

    return coherence_lda

def preprocess(text: str) -> List[str]:
    lemmatizer = WordNetLemmatizer()

    def lemmatize_stemming(token):
        return lemmatizer.lemmatize(token, pos='v')

    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3:
            result.append(lemmatize_stemming(token))
    return result


def readability(content: str) -> float:
    flesch_reading_ease = textstat.flesch_reading_ease(content)
    return flesch_reading_ease


def grammar_and_spelling(content: str) -> float:
    matches = tool.check(content)
    grammar_score = 1 - len(matches) / len(content)
    return grammar_score


def length(content: str) -> float:
    # Calculate the length score based on your preferred content length
    preferred_length = 500
    length_score = 1 - abs(len(content) - preferred_length) / preferred_length
    return length_score


@internal_error_handler
def update_content(user_id, user_name, content_id, message):
    content_data = (
        Content.query.filter(
            Content.id == content_id,
            Content.user_id == user_id,
            Content.status == constants.ContentStatus.SUCCESS,
        ).first()
    )

    system_message = {
        "role": "system",
        "content": "You are a highly specialised content creator GPT. We have generated content for user and then interacted with user to understand his needs. User has provided the feedback on changes that needs to be done in content. Your job is to provide a new content.",
        "name": "AIsstant Hub",
    }

    user_message = {
        "role": "user",
        "content": f"{content_data.model_response}\n\n\"{message}\"",
        "name": user_name,
    }

    assistant_response = openai.ChatCompletion.create(
        model=Config.OPENAI_MODEL,
        messages=[system_message, user_message],
        temperature=0.7,
        n=5,
        presence_penalty=0,
        user=str(user_id),
        frequency_penalty=0,
    )
    print(assistant_response)
    print("/n/n/n")

    contents_by_model = [resp_data["message"]["content"] for resp_data in assistant_response["choices"]]
    print(contents_by_model)
    best_content_data = best_content(user_message["name"], contents_by_model)
    print(best_content_data)

    return response(
        success=True,
        message="Content generated.",
        content=best_content,
    )
