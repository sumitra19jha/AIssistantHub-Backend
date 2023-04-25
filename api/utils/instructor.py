from api.models import db

from api.assets.constants import ChatPrompt
from api.utils.chat_db import ChatDataModelUtil
from api.utils.dashboard import DashboardUtils


class Instructor:
    def handle_chat_instruction_for_social_media(name_of_user, content_data, is_opinion, web_searched_results=None):
        system_chat_prompt = ChatPrompt.social_media_system_chat_prompt()
        
        if is_opinion:
            web_content = ""
            for result in web_searched_results:
                web_content = web_content + result['website'] + ", "

            # Remove the trailing comma and space
            web_content = web_content.rstrip(', ')
            
            user_prompt_generated_by_system = ChatPrompt.social_media_user_chat_prompt_by_system_for_opinion(
                platform=DashboardUtils.format_string_for_chat(content_data.platform),
                topic=DashboardUtils.format_string_for_chat(content_data.topic),
                user_name=name_of_user,
                type=DashboardUtils.format_string_for_chat(content_data.type),
                websites=web_content,
            )
        else:
            user_prompt_generated_by_system = ChatPrompt.social_media_user_chat_prompt_by_system(
                platform=DashboardUtils.format_string_for_chat(content_data.platform),
                topic=DashboardUtils.format_string_for_chat(content_data.topic),
                user_name=name_of_user,
                type=DashboardUtils.format_string_for_chat(content_data.type),
            )

        system_chat_instruction = ChatDataModelUtil.set_chat_instruction_for_system_from_content(content_data, system_chat_prompt)
        user_chat_initiation = ChatDataModelUtil.initiate_chat_for_user_from_content(content_data, user_prompt_generated_by_system)

        db.session.add_all([system_chat_instruction, user_chat_initiation])
        db.session.commit()

    def handle_chat_instruction(name_of_user, content_data):
        system_chat_prompt = f"You are now an assistant content creator GPT called 'IntelliMate' working for KeywordIQ Company. You are doing a real time communication with our client to make optimize SEO of content. The content is below: {content_data.model_response}"
        user_prompt_generated_by_system = f"Hi I am {name_of_user}."

        system_chat_instruction = ChatDataModelUtil.set_chat_instruction_for_system_from_content(content_data, system_chat_prompt)
        user_chat_initiation = ChatDataModelUtil.initiate_chat_for_user_from_content(content_data, user_prompt_generated_by_system)

        db.session.add_all([system_chat_instruction, user_chat_initiation])
        db.session.commit()