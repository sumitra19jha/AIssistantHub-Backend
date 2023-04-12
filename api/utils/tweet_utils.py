# pyright: reportMissingImports=false
import torch
import spacy
import fasttext
import re

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from googletrans import Translator
from gensim.summarization import keywords as gensim_keywords
from transformers import AutoTokenizer, AutoModelForSequenceClassification, BartForSequenceClassification, BartTokenizer, pipeline

from api.assets.tweet_constants import TweetCategory

# 1. Load pre-trained facebook/bart-large-mnli model for Classification of Topic
classifier_model_name = "facebook/bart-large-mnli"
classifier_model = BartForSequenceClassification.from_pretrained(classifier_model_name)
classifier_tokenizer = BartTokenizer.from_pretrained(classifier_model_name)
classifier = pipeline("zero-shot-classification", model=classifier_model, tokenizer=classifier_tokenizer)

# 2. Load pre-trained BERT model for sentiment analysis
sentiment_model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer_for_sentiment = AutoTokenizer.from_pretrained(sentiment_model_name)
model_for_sentiment = AutoModelForSequenceClassification.from_pretrained(sentiment_model_name)

# 4. Load pre-trained SpaCy model for Named Entity Recognition
nlp = spacy.load("en_core_web_sm")

# 5. Load pre-trained FastText language model for Language detection
language_model_path = "/Users/sumitra/Desktop/ChatGPT/New_Project/Backend/lid.176.bin"
language_model = fasttext.load_model(language_model_path)


class TweetUtils:
    @staticmethod
    def create_gpt_prompt(topic, category, sentiment, keywords, entities, tweet_length, additional_instructions=None):
        prompt = f"Generate {tweet_length} about '{topic}'"
        if entities:
            entity_str = ', '.join([ent['text'] for ent in entities])
            prompt += f" ({entity_str})"
        
        if keywords:
            keyword_str = ', '.join(keywords)
            prompt += f" with focus on {keyword_str}"
        
        if category:
            prompt += f" in the context of {category}"
        
        if sentiment:
            prompt += f" with a {sentiment.lower()} sentiment."

        if additional_instructions:
            prompt += additional_instructions

        return prompt

    @staticmethod
    def preprocess_text(text):
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|@\w+|[^\w\s]', '', text) # Remove URLs, mentions, and special characters
        tokens = word_tokenize(text) # Tokenize the text

        # Remove only the most common stopwords
        stop_words = set(stopwords.words('english'))

        tokens = [token for token in tokens if token not in stop_words] # Remove important stopwords

        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens] # Lemmatize the tokens

        preprocessed_text = ' '.join(tokens) # Rejoin the tokens into a single string
        return preprocessed_text
    
    @staticmethod
    def classify_tweet(tweet):
        result = classifier(tweet, candidate_labels=TweetCategory.all())
        best_category = result["labels"][0]
        return best_category
    
    # For our use case, we will use the cardiffnlp/twitter-roberta-base-sentiment model
    # which is fine-tuned for sentiment analysis on tweets and has three sentiment classes.
    @staticmethod
    def analyze_sentiment(tweet):
        inputs = tokenizer_for_sentiment(tweet, return_tensors="pt")
        outputs = model_for_sentiment(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=1).tolist()[0]
        sentiment_index = probabilities.index(max(probabilities))
        return ["Negative", "Neutral", "Positive"][sentiment_index]
    
    # Define the keyword extraction function
    @staticmethod
    def extract_keywords(text, num_keywords=2):
        extracted_keywords = gensim_keywords(text, words=num_keywords, lemmatize=True)
        keyword_list = extracted_keywords.split('\n')
        return keyword_list
    

    # Keep in mind that this example uses the small English model (en_core_web_sm). 
    # You can use other pre-trained models, like en_core_web_md or en_core_web_lg, for improved accuracy. 
    # Remember to install the required model before using it:
    # ```
    #    python -m spacy download en_core_web_md
    # ```
    @staticmethod
    def extract_entities(text):
        doc = nlp(text)
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        return entities
    

    # Define the language detection function
    @staticmethod
    def detect_language(text):
        predictions = language_model.predict(text)
        language = predictions[0][0].replace("__label__", "")
        return language
    
    @staticmethod
    def translate_text(text, detected_language, target_language='en'):
        if detected_language == target_language:
            return text

        translator = Translator()
        translated_text = translator.translate(text, src=detected_language, dest=target_language).text
        return translated_text

