import openai

from config import Config
from api.assets import constants
from api.utils import logging_wrapper

logger = logging_wrapper.Logger(__name__)

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
            total_tokens = assistant_response['usage']['total_tokens']
            return assistant_response, total_tokens
        except Exception as e:
            return None, 0

    def generate_title_templates(user, business_type, target_audience, industry, location, num_templates=5):
        try:
            prompt = f"Generate {num_templates} content title templates for a {business_type} business targeting {target_audience} in the {industry} industry located in {location}. Include a '{{keyword}}' placeholder in each template where a keyword will be inserted."
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.7,
                max_tokens=100,
                n=1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            # Extract and format search queries as an array
            search_queries = response.choices[0].text.strip().split("\n")
            return search_queries
        except Exception as e:
            return None
    
    def generate_youtube_search_text(user, business_type, target_audience, industry, location):
        try:
            prompt = f"Generate YouTube search queries based on the following information:\n1. Business type: {business_type}\n2. Target audience: {target_audience}\n3. Industry: {industry}\n4. Location: {location}\n\nSearch queries:"
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.7,
                max_tokens=100,
                n=1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            # Extract and format search queries as an array
            search_queries = response.choices[0].text.strip().split("\n")
            return search_queries
        except Exception as e:
            print(f"Error: {e}")
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