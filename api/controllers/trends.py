import tweepy
import os
from pytrends.request import TrendReq

def fetch_twitter_trends():
    consumer_key = os.environ['TWITTER_CONSUMER_KEY']
    consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
    access_token = os.environ['TWITTER_ACCESS_TOKEN']
    access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    # Replace 1 with the Yahoo! Where On Earth ID (WOEID) for your desired location
    trends = api.trends_place(1)

    # Extract and return the trending keywords
    return [trend['name'] for trend in trends[0]['trends']]


def fetch_google_trends():
    pytrends = TrendReq(hl='en-US', tz=360)

    # Fetch the top queries for the past 24 hours
    top_queries = pytrends.today_searches()

    # Return the trending keywords
    return top_queries.tolist()
