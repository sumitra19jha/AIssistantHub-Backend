from api.assets import constants
from api.models.chat import Chat


class ChatDataModelUtil:
    def set_chat_instruction_for_system_from_content(content_data, system_chat_prompt):
        return Chat(
            content_id=content_data.id,
            user_id=content_data.user_id,
            type=constants.ChatTypes.SYSTEM,
            hidden=True,
            message=system_chat_prompt,
        )

    def initiate_chat_for_user_from_content(content_data, user_prompt_generated_by_system):
        return Chat(
            content_id=content_data.id,
            user_id=content_data.user_id,
            type=constants.ChatTypes.USER,
            hidden=True,
            message=user_prompt_generated_by_system,
        )