from http import HTTPStatus
from api.utils.request import bad_response, response

from api.assets import constants

class APIInputValidator:
    def validate_input_for_seo(business_type, target_audience, industry, goals):
        if not (business_type and isinstance(business_type, str) and len(business_type) > 0):
            return response(
                success=False,
                message="Bussiness type is not provided or empty",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        
        if not (target_audience and isinstance(target_audience, str) and len(target_audience) > 0):
            return response(
                success=False,
                message="Target audience is not provided or empty",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if not (industry and isinstance(industry, str) and len(industry) > 0):
            return response(
                success=False,
                message="Industry is not provided or empty",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if not (goals and len(goals) > 0):
            return response(
                success=False,
                message="Goals are not provided or empty selection",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        
        return None
    
    def validate_content_input_for_social_media(topic, platform, length):
        if not (platform and platform in ['LINKEDIN', 'TWITTER', 'FACEBOOK', 'INSTAGRAM']):
            return response(
                success=False,
                message="Incorrect platform provided.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if not (topic and isinstance(topic, str)):
            return response(
                success=False,
                message="Topic of content is not provided.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if not (length and length in constants.ContentLengths.all()):
            return response(
                success=False,
                message="Length of content is not provided.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        return None

    def validate_content_input(type, topic, length):
        if not (type and type in constants.ContentTypes.all()):
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

        if not (length and length in constants.ContentLengths.all()):
            return response(
                success=False,
                message="Length of content is not provided.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        return None