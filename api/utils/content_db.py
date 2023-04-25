from api.assets import constants
from api.models.content import Content
from config import Config
from api.models import db


class ContentDataModel:
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

    def update_content_model_after_successful_ai_response(assistant_response, content_data):
        content_data.model_response = assistant_response['choices'][0]['message']['content']
        content_data.content_data = assistant_response['choices'][0]['message']['content']
        content_data.no_of_prompt_tokens = assistant_response['usage']['prompt_tokens']
        content_data.no_of_completion_tokens = assistant_response['usage']['completion_tokens']
        content_data.finish_reason = assistant_response['choices'][0]['finish_reason']
        content_data.status = constants.ContentStatus.SUCCESS
        db.session.commit()
        return True

    def update_content_model_after_failed_ai_response(content_data):
        content_data.status = constants.ContentStatus.ERROR
        db.session.commit()
        return False