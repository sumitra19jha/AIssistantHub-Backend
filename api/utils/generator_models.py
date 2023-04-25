import openai
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