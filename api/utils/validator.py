from http import HTTPStatus
from api.utils.request import bad_response, response

from api.assets import constants

class APIInputValidator:
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