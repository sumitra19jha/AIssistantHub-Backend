import openai

class ClassifierModels:
    def is_the_topic_opinion_based(topic):
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Topic: \"{topic}\"\n\nIs this topic an opinion based topic? Yes or No\nAns:",
                temperature=0.7,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            response_text = str(response['choices'][0]["text"]).lower()
            if 'yes' in response_text:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False