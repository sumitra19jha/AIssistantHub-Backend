from http import HTTPStatus
import openai
import tiktoken
from config import Config

from api.assets import constants
from api.models.content import Content
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



@internal_error_handler
def generate_content(user, type, topic, keywords, length):
    if (type == None) or type not in [
        constants.ContentTypes.ARTICLE, 
        constants.ContentTypes.BLOG_POST, 
        constants.ContentTypes.LISTICLE, 
        constants.ContentTypes.TWEET, 
        constants.ContentTypes.VIDEO_SCRIPT
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

    system_message = f"You are a {type} writing GPT working for KeywordIQ. You are writing for our client who expects a good SEO based {type}."
    user_message = f"Write a {type} on {topic}. The length of the topic should be {length}. Include all these keywords: {keywords}"

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
        print(e);
        content_data.status = constants.ContentStatus.ERROR
        db.session.commit()
        return response(
            success=False,
            message="Unable to generate the content.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    db.session.commit()

    return response(
        success=True, 
        message=constants.SuccessMessage.content_generated, 
        content=content_data.model_response,
    )