import openai

from api.assets import constants
from config import Config

class GeneratorModels:
    def generate_content(user, system_message, user_message):
        try:
            assistant_response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                top_p=1,
                presence_penalty=0,
                user=str(user.id),
                frequency_penalty=0,
            )
            return assistant_response
        except Exception as e:
            return None
    
    def generate_youtube_search_text(user, bussiness_type, target_audience, industry, goals, location):
        try:
            assistant_response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a Youtube Search GPT, an AI that provides search text in the form of an array based on user input for the purpose of examining popular videos and channels to identify the content preferences of target audiences.\n\nYour output will be in the form of an array with search texts.",
                    },
                    {
                        "role": "user",
                        "content": f"User Input\n```\n1. Business type: {bussiness_type}\n2. Target audience: {target_audience}\n3. Industry: {industry}\n4. Goals: {goals}\n5. Location: {location}\n```",
                    }, 
                ],
                temperature=0.7,
                top_p=1,
                presence_penalty=0,
                user=str(user.id),
                frequency_penalty=0,
            )
            return assistant_response["choices"][0]["message"]["content"]
        except Exception as e:
            return None
        
    def generate_news_search_text(user, bussiness_type, target_audience, industry, goals, location):
        try:
            assistant_response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a News Search GPT, an AI that provides Google search text in the form of an array based on user input for the purpose to find niche news articles to identify trends, events, and industry developments.\n\nYour output will be in the form of an array with search texts. Make sure the search text has news keyword.",
                    },
                    {
                        "role": "user",
                        "content": f"User Input\n```\n1. Business type: {bussiness_type}\n2. Target audience: {target_audience}\n3. Industry: {industry}\n```",
                    }, 
                ],
                temperature=0.7,
                top_p=1,
                presence_penalty=0,
                user=str(user.id),
                frequency_penalty=0,
            )
            return assistant_response["choices"][0]["message"]["content"]
        except Exception as e:
            return None