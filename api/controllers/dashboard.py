import openai
from bs4 import BeautifulSoup
from http import HTTPStatus

from config import Config
from api.utils.socket import Socket

from api.assets import constants
from api.assets.constants import ContentLengths, ContentStatus, ContentTypes, ChatTypes, ContentPrompt, ChatPrompt, SuccessMessage
from api.models.content import Content
from api.models.chat import Chat
from api.models import db

from api.utils.time import TimeUtils
from api.utils.tweet_utils import TweetUtils
from api.utils.dashboard import DashboardUtils

from api.utils.request import bad_response, response
from api.middleware.error_handlers import internal_error_handler


@internal_error_handler
def generate_content(user, type, topic, platform, purpose, keywords, length):
    validation_response = validate_content_input(type, topic, length)
    if validation_response:
        return validation_response

    content_length = DashboardUtils.sizeOfContent(type, length)
    system_message, user_message = generate_messages(
        type,
        topic,
        platform,
        length,
        content_length,
        purpose
    )

    content_data = create_content_data(
        user, 
        type, 
        topic, 
        platform, 
        purpose, 
        keywords, 
        length, 
        system_message, 
        user_message
    )
    assistant_response = get_assistant_response(
        user, 
        system_message, 
        user_message, 
        content_data
    )

    if assistant_response:
        handle_chat_instruction(user.name, content_data)

        # Call the Node.js server to create a room
        Socket.create_room_for_content(content_data.id, content_data.user_id)

        return response(
            success=True,
            message=SuccessMessage.content_generated,
            content=content_data.model_response,
            contentId=content_data.id,
        )
    else:
        return response(
            success=False,
            message="Unable to generate the content.",
            status_code=HTTPStatus.BAD_REQUEST,
        )


def validate_content_input(type, topic, length):
    if not (type and type in ContentTypes.all()):
        return response(
            success=False,
            message="Type of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if not (topic and isinstance(topic, str)):
        return response(
            success=False,
            message="Topic of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if not (length and length in ContentLengths.all()):
        return response(
            success=False,
            message="Length of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    return None


def generate_messages(type, topic, platform, length, content_length, purpose):
    if type == ContentTypes.SOCIAL_MEDIA_POST and platform == "LINKEDIN":
        system_message = ContentPrompt.linkedin_system_message
        user_message = ContentPrompt.linkedin_user_message(
            topic=topic, content_length=content_length)

    elif type == ContentTypes.SOCIAL_MEDIA_POST and platform == "TWITTER":
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

    elif type == ContentTypes.SOCIAL_MEDIA_POST:
        system_message = ContentPrompt.social_media_post_system_message(
            platform=platform, topic=topic, content_length=content_length)
        user_message = ContentPrompt.social_media_post_user_message(
            platform=platform, topic=topic, content_length=content_length)

    else:
        system_message = f"You are a {type} writing GPT working for KeywordIQ. You are directly writing for our client."
        user_message = f"Write a {type} on {topic}. The length of the content should be {content_length}.\nThe purpose of the content is to {purpose}.\nYour writing should be in visually appealing HTML as it is shown directly on our platform."

    return system_message, user_message


def create_content_data(user, type, topic, platform, purpose, keywords, length, system_message, user_message):
    content_data = Content(
        user_id=user.id,
        type=type,
        topic=topic,
        keywords=keywords,
        length=length,
        system_message=system_message,
        user_message=user_message,
        model=Config.OPENAI_MODEL,
        platform=platform,
        purpose=purpose,
    )
    db.session.add(content_data)
    db.session.flush()
    return content_data


def get_assistant_response(user, system_message, user_message, content_data):
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
        content_data.model_response = assistant_response['choices'][0]['message']['content']
        content_data.no_of_prompt_tokens = assistant_response['usage']['prompt_tokens']
        content_data.no_of_completion_tokens = assistant_response['usage']['completion_tokens']
        content_data.finish_reason = assistant_response['choices'][0]['finish_reason']
        content_data.status = ContentStatus.SUCCESS
        db.session.commit()
        return True
    except Exception as e:
        content_data.status = ContentStatus.ERROR
        db.session.commit()
        return False


def handle_chat_instruction(name_of_user, content_data):
    if content_data.type == ContentTypes.SOCIAL_MEDIA_POST:
        system_chat_prompt = ChatPrompt.social_media_system_chat_prompt()

        user_prompt_generated_by_system = ChatPrompt.social_media_user_chat_prompt_by_system(
            platform=' '.join(word.capitalize() for word in content_data.platform.replace('_', ' ').split(' ')),
            topic=' '.join(word.capitalize() for word in content_data.topic.replace('_', ' ').split(' ')),
            user_name=name_of_user,
            type=' '.join(word.capitalize() for word in content_data.type.replace('_', ' ').split(' ')),
        )
    else:
        system_chat_prompt = f"You are now an assistant content creator GPT called 'IntelliMate' working for KeywordIQ Company. You are doing a real time communication with our client to make optimize SEO of content. The content is below: {content_data.model_response}"
        user_prompt_generated_by_system = f"Hi I am {name_of_user}."

    system_chat_instruction = Chat(
        content_id=content_data.id,
        user_id=content_data.user_id,
        type=ChatTypes.SYSTEM,
        hidden=True,
        message=system_chat_prompt,
    )

    user_chat_initiation = Chat(
        content_id=content_data.id,
        user_id=content_data.user_id,
        type=ChatTypes.USER,
        hidden=True,
        message=user_prompt_generated_by_system,
    )

    db.session.add_all([system_chat_instruction, user_chat_initiation])
    db.session.commit()


@internal_error_handler
def content_history(user):
    contents_data = (
        Content.query.filter(
            Content.user_id == user.id,
            Content.status == constants.ContentStatus.SUCCESS,
        )
        .order_by(Content.created_at.desc())
        .all()
    )

    history = []
    for content in contents_data:
        # Create a BeautifulSoup object to parse the HTML content
        soup = BeautifulSoup(content.model_response, "html.parser")

        # Get only the text content of the page
        model_response_text = soup.get_text()
        created_at = TimeUtils.time_ago(content.created_at)

        history.append({
            "content_id": content.id,
            "created_at": created_at,
            "type": content.type,
            "topic": content.topic,
            "length": content.length,
            "model_response": model_response_text,
            "html_form": content.model_response,
        })

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        history=history,
    )


@internal_error_handler
def content_chat_history(user, content_id):
    chats_data = (
        Chat.query.filter(
            Chat.content_id == content_id,
            Chat.hidden == False,
            Chat.type != constants.ChatTypes.SYSTEM,
        )
        .all()
    )

    history = []
    for chat in chats_data:
        history.append({
            "id": chat.id,
            "type": "ai" if chat.type == constants.ChatTypes.AI else "user",
            "content": chat.message,
            "username": "Proton" if chat.type == constants.ChatTypes.AI else user.name,
            "timestamp": chat.created_at,
        })

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        history=history,
    )
