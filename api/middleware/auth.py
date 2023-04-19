from datetime import datetime as dt
from functools import wraps
from http import HTTPStatus
from flask import request

from api.assets import constants
from api.utils.request import bad_response, response
from api.utils import logging_wrapper
from api.models.session import Session
from marshmallow import ValidationError

from config import Config

logger = logging_wrapper.Logger(__name__)


def authenticate_all(f):
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization", None)
            if auth_header is None:
                return response(
                    success=False,
                    message="Authentication Error: Auth header missing.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )
            auth_header_tokens = auth_header.split()
            if len(auth_header_tokens) != 2:
                return response(
                    success=False,
                    message="Authentication Error: Auth header invalid.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )
            _, session_id = auth_header_tokens

            
            session = Session.query.filter(Session.session_id == session_id).first()
            if (
                session is not None
                and session.status == constants.SessionCons.enum_active
                and session.valid_till is not None
                and session.valid_till >= dt.utcnow()
            ):
                user = session.user
                if (
                    user.status != constants.UserCons.enum_status_deleted
                ):
                    request.session_id = session_id
                    request.session, request.user = session, user
                    return f(*args, **kwargs)
            return response(
                success=False,
                message="Authentication Error: Invalid Session",
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except ValidationError as e:
            logger.exception(str(e))
            raise e
        except Exception as e:
            logger.exception(str(e))
            return response(
                success=False,
                message="Internal Server Error: Authentication Module",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    return wrapped_function


def authenticate(f):
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization", None)
            if auth_header is None:
                return response(
                    success=False,
                    message="Authentication Error: Auth header missing.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )
            auth_header_tokens = auth_header.split()
            if len(auth_header_tokens) != 2:
                return response(
                    success=False,
                    message="Authentication Error: Auth header invalid.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )
            _, session_id = auth_header_tokens
            
            session = Session.query.filter(Session.session_id == session_id).first()
            if (
                session is not None
                and session.status == constants.SessionCons.enum_active
                and session.valid_till is not None
                and session.valid_till >= dt.utcnow()
            ):
                user = session.user
                if (
                    user.status != constants.UserCons.enum_status_deleted
                ):
                    request.session_id = session_id
                    request.session, request.user = session, user
                    return f(*args, **kwargs)
            return response(
                success=False,
                message="Authentication Error: Invalid Session",
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except ValidationError as e:
            logger.exception(str(e))
            raise e
        except Exception as e:
            logger.exception(str(e))
            return response(
                success=False,
                message="Internal Server Error: Authentication Module",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    return wrapped_function


def authenticate_internal_rtc_backend(f):
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization", None)
            if auth_header is None:
                return response(
                    success=False,
                    message="Authentication Error: Auth header missing.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )

            auth_header_tokens = auth_header.split()
            if len(auth_header_tokens) != 2:
                return response(
                    success=False,
                    message="Authentication Error: Auth header invalid.",
                    status_code=HTTPStatus.UNAUTHORIZED,
                )

            _, rtc_key = auth_header_tokens
            if rtc_key == Config.RTC_AUTH_KEY:
                return f(*args, **kwargs)

            return response(
                success=False,
                message="Authentication Error: Invalid private key",
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except Exception as e:
            logger.exception(str(e))
            return response(
                success=False,
                message="Internal Server Error: Authentication Module, private key",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    return wrapped_function