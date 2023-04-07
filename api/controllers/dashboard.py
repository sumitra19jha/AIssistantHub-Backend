from http import HTTPStatus
from api.utils.socket import Socket
import openai
import tiktoken
import requests
import uuid
from config import Config

from api.assets import constants
from api.models.content import Content
from api.models.chat import Chat
from api.models import db

from api.utils.request import bad_response, response
from api.middleware.error_handlers import internal_error_handler


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")



def generate_unique_room_id():
    return str(uuid.uuid4())


@internal_error_handler
def generate_content(user, type, topic, platform, purpose, keywords, length):
    if (type == None) or type not in [
        constants.ContentTypes.SOCIAL_MEDIA_POST,
        constants.ContentTypes.BLOG_POST,
        constants.ContentTypes.ARTICLE,
        constants.ContentTypes.EMAIL_MARKETING,
        constants.ContentTypes.NEWS_LETTER,
        constants.ContentTypes.PRODUCT_DESCRIPTION,
        constants.ContentTypes.CASE_STUDY,
        constants.ContentTypes.WHITE_PAPER,
        constants.ContentTypes.LISTICLE,
        constants.ContentTypes.VIDEO_SCRIPT,
        constants.ContentTypes.WEBINAR_SCRIPT,
        constants.ContentTypes.EDUCATIONAL_CONTENT,
    ]:
        return response(
            success=False,
            message="Type of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    if (topic == None) or (not isinstance(topic, str)):
        return response(
            success=False,
            message="Topic of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    if (length == None) or length not in [
        constants.ContentLengths.SHORT, 
        constants.ContentLengths.MEDIUM, 
        constants.ContentLengths.LONG,
    ]:
        return response(
            success=False,
            message="Length of content is not provided.",
            status_code=HTTPStatus.BAD_REQUEST,
        )    
    
    content_length = sizeOfContent(type, length)

    system_message = f"You are a {type} writing GPT working for KeywordIQ. You are directly writing for our client."
    user_message = f"Write a {type} on {topic}. The length of the content should be {content_length}.\nThe purpose of the content is to {purpose}.\nYour writing should be in visually appealing HTML as it is shown directly on our platform."

    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content":user_message},
    ]

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
        purpose=platform,
    )

    db.session.add(content_data)
    db.session.flush()

    try:
        assistant_response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            user=str(user.id),
        )

        content_data.model_response = assistant_response['choices'][0]['message']['content']
        content_data.no_of_prompt_tokens = assistant_response['usage']['prompt_tokens']
        content_data.no_of_completion_tokens = assistant_response['usage']['completion_tokens']
        content_data.finish_reason = assistant_response['choices'][0]['finish_reason']
        content_data.status = constants.ContentStatus.SUCCESS
    except Exception as e:
        content_data.status = constants.ContentStatus.ERROR
        db.session.commit()
        return response(
            success=False,
            message="Unable to generate the content.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    db.session.commit()

    # Call the Node.js server to create a room
    Socket.create_room_for_content(content_data.id, content_data.user_id)

    return response(
        success=True, 
        message=constants.SuccessMessage.content_generated, 
        content=content_data.model_response,
        contentId=content_data.id,
    )


def sizeOfContent(type, length):
    if type == constants.ContentTypes.SOCIAL_MEDIA_POST:
        if length == constants.ContentLengths.SHORT:
            return "50 - 100 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "100 - 200 words"
        else:
            return "200 - 300 words"
    elif (type == constants.ContentTypes.BLOG_POST) or (type == constants.ContentTypes.ARTICLE) or (type == constants.ContentTypes.LISTICLE):
        if length == constants.ContentLengths.SHORT:
            return "300 - 500 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "500 - 1,200 words"
        else:
            return "1,200 - 2,500+ words"
    elif (type == constants.ContentTypes.EMAIL_MARKETING) or (type == constants.ContentTypes.NEWS_LETTER):
        if length == constants.ContentLengths.SHORT:
            return "100 - 200 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "200 - 500 words"
        else:
            return "500 - 1,000 words"
    elif (type == constants.ContentTypes.PRODUCT_DESCRIPTION):
        if length == constants.ContentLengths.SHORT:
            return "50 - 100 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "100 - 200 words"
        else:
            return "200 - 400 words"
    elif (type == constants.ContentTypes.CASE_STUDY):
        if length == constants.ContentLengths.SHORT:
            return "500 - 1,000 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "1,000 - 2,000 words"
        else:
            return "2,000 - 5,000+ words"
    elif (type == constants.ContentTypes.VIDEO_SCRIPT):
        if length == constants.ContentLengths.SHORT:
            return "100 - 200 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "200 - 600 words"
        else:
            return "600 - 1,200+ words"
    else:
        if length == constants.ContentLengths.SHORT:
            return "300 - 500 words"
        elif length == constants.ContentLengths.MEDIUM:
            return "500 - 1,200 words"
        else:
            return "1,200 - 2,500+ words"