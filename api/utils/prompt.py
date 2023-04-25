from api.assets.constants import ContentPrompt
from api.utils.tweet_utils import TweetUtils


class PromptGenerator:
    def generate_messages_on_opinion_for_social_media(topic, platform, content_length, web_content):
        if platform == "LINKEDIN":
            system_message = ContentPrompt.linkedin_system_message_for_opinion
            user_message = ContentPrompt.linkedin_user_message_for_opinion(
                topic=topic, 
                websites_content=web_content, 
                content_length=content_length,
            )

        return system_message, user_message

    def generate_messages_for_social_media(topic, platform, length, content_length):
        if platform == "LINKEDIN":
            system_message = ContentPrompt.linkedin_system_message
            user_message = ContentPrompt.linkedin_user_message(
                topic=topic, 
                content_length=content_length,
            )

        elif platform == "TWITTER":
            # Add a dictionary mapping the tweet_length values to descriptions
            length_descriptions = {
                "SHORT": "a short engaging tweet",
                "MEDIUM": "a medium-length engaging tweet",
                "LONG": "a series of engaging tweets in a thread",
            }

            # 1. GET THE LANGUAGE FROM THE TOPIC
            language_for_tweet = TweetUtils.detect_language(topic)
            translated_topic = TweetUtils.translate_text(topic, language_for_tweet)

            preprocessed_topic = TweetUtils.preprocess_text(translated_topic)

            # 2. GET UNDER WHICH CATEGORY THE TWEET COMES IN
            category_for_tweet = TweetUtils.classify_tweet(preprocessed_topic)

            # 3. GET THE SENTIMENT FOR THE TWEET
            sentiment_for_tweet = TweetUtils.analyze_sentiment(preprocessed_topic)

            # 4. GET THE KEYWORDS FROM THE TOPIC
            keyword_for_tweet = TweetUtils.extract_keywords(preprocessed_topic)

            # 5. GET THE NAMED ENTITY FROM THE TOPIC
            named_entity_for_tweet = TweetUtils.extract_entities(
                preprocessed_topic)

            system_message = "You are a Tweet writing GPT. A highly trained AI model working for KeywordIQ. You are directly writing for our client, so only provide Tweet in your response."
            user_message = TweetUtils.create_gpt_prompt(
                category=category_for_tweet,
                entities=named_entity_for_tweet,
                keywords=keyword_for_tweet,
                sentiment=sentiment_for_tweet,
                topic=translated_topic,  # Use the original translated topic
                tweet_length=length_descriptions[length],
                additional_instructions=None if length != "LONG" else "\n\nYou can follow the below rules to create a good tweet thread:\n\n1. Outline the thread\'s structure. Determine the key points to cover and organize them in a logical sequence. This will help you create a cohesive narrative and keep your thread focused\n\n2. Begin with a hook: Start your thread with an engaging and informative Tweet that captures the attention of your audience. Introduce the topic and provide a brief overview of what the thread will cover.\n\n3. Be concise: Each Tweet in the thread should be clear and concise, focusing on one main point. Remember that you have a 280-character limit, so use words wisely.\n\n4. Use GIFs or emojis: Enhance the thread with relevant GIFs, or emojis to provide context and keep the audience engaged. Visual elements can help to break up long blocks of text and make the thread more appealing.\n\n5. Number your Tweets: Numbering Tweets (e.g., \"1/5\", \"2/5\", etc.) help the audience follow the thread more easily and indicates how many parts there are in the thread.\n\n6. Maintain consistency: Keep writing style, tone, and formatting consistent throughout the thread. This makes it easier for the audience to follow along and understand your message.\n\n7. End with a conclusion: Wrap up the thread with a concise summary, conclusion, or call to action. This gives the audience a clear takeaway and invites further engagement.",
            )

        else:
            system_message = ContentPrompt.social_media_post_system_message(
                platform=platform, 
                topic=topic, 
                content_length=content_length,
            )
            user_message = ContentPrompt.social_media_post_user_message(
                platform=platform, 
                topic=topic, 
                content_length=content_length,
            )
        
        return system_message, user_message

    def generate_messages(type, topic, content_length, purpose):
        system_message = f"You are a {type} writing GPT working for KeywordIQ. You are directly writing for our client."
        user_message = f"Write a {type} on {topic}. The length of the content should be {content_length}.\nThe purpose of the content is to {purpose}.\nYour writing should be in visually appealing HTML as it is shown directly on our platform."

        return system_message, user_message
