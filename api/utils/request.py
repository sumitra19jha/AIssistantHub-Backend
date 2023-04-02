from http import HTTPStatus
import json
from flask import jsonify
from api.utils import logging_wrapper


logger = logging_wrapper.Logger(__name__)


def response(success, message, status_code=200, response_dict={}, **kwargs):
    return (
        jsonify({"success": success, "message": message, **kwargs, **response_dict}),
        status_code,
    )


def bad_response(message, **kwargs):
    return response(
        success=False, message=message, status_code=HTTPStatus.BAD_REQUEST, **kwargs
    )


def success_response(message, **kwargs):
    return response(success=True, message=message, status_code=HTTPStatus.OK, **kwargs)

def get_parsed_data_list(request, key_list):
    return [request.json.get(key, None) for key in key_list]


def get_parsed_list(mapping, key_list, default_value=None):
    return [mapping.get(key, default_value) for key in key_list]


def decode_response(response_):
    return json.loads(response_[0].get_data().decode("utf-8"))


def is_not_blank(s):
    return bool(s and not s.isspace())


def is_blank(s):
    return not bool(s and not s.isspace())


def log_response(res):
    try:
        if not res.ok:
            logable_data = res.json()
            logger.error({**res.__dict__, "json": logable_data})
    except Exception as e:
        logger.error(res.__dict__)
