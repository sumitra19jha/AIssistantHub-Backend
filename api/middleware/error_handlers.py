import traceback
from functools import wraps
from http import HTTPStatus

from api.assets.constants import ErrorMessage
from api.assets.constants import LogScope

from api.utils.request import response
from api.utils import logging_wrapper

logger = logging_wrapper.Logger(__name__)

def internal_error_handler(f):
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # NOTE: Keeping print for debug purposes, in case sentry doesn't work as intended.
            # print(f"Internal server error: Exception occurred", e)
            logger.exception(str(e))
            return response(
                False,
                ErrorMessage.internal_server_error,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    return wrapped_function