import os
import sys
import nltk
import openai
import decimal
import traceback
from functools import wraps

from flasgger import Swagger, swag_from
from flask_cors import CORS
from flask.json import JSONEncoder
from marshmallow import ValidationError
from flask import Flask, Response, request

from api.models import db
from api.utils import logging_wrapper
from api.utils.error_classes import BaseClientError
from api.routes.home import bp as home_bp
from api.routes.user import bp as user_bp
from api.routes.dashboard import bp as dashboard_bp
from api.routes.analysis import bp as analysis_bp
from api.routes.content import bp as content_bp
from config import Config


openai.api_key = Config.OPENAI_API_KEY


def download_nltk_resources():
    nltk_resources = ['punkt', 'wordnet', 'stopwords']
    for resource in nltk_resources:
        try:
            nltk.data.find(f'corpora/{resource}')
            print(f"{resource} already downloaded.")
        except LookupError:
            try:
                nltk.download(resource)
                print(f"{resource} downloaded successfully.")
            except LookupError:
                print(f"Error downloading {resource}. Please try again.")


class JsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return JSONEncoder.default(self, obj)


"""
Logger
"""
logger = logging_wrapper.Logger(__name__)

app = Flask(__name__)
app.json_encoder = JsonEncoder
CORS(app)


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(error):
    if isinstance(error.messages, list):
        error.messages = {"validation": error.messages}
    return {
        "success": False,
        "message": "Validation Error: One or more input fields are incorrect",
        "errors": error.messages,
    }, 400


@app.errorhandler(BaseClientError)
def handle_not_found_error(error):
    return {
        "success": False,
        "message": error.message,
        "code": error.code,
    }, error.status_code


def requires_basic_auth(f):
    """Decorator to require HTTP Basic Auth for your endpoint."""

    def check_auth(username, password):
        return username == Config.SWAGGER_USERNAME and password == Config.SWAGGER_PASSWORD

    def authenticate():
        return Response(
            "Authentication required.",
            401,
            {"WWW-Authenticate": "Basic realm='Login Required'"},
        )

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


app.config["SWAGGER"] = {
    "title": "Backend APIs",
    "uiversion": 3,
    "description": "This is a KeywordIQ Backend APIs",
    "version": "1.0.0",
    "termsOfService": "link here",
    "contact": {"email": Config.SWAGGER_EMAIL},
    "ui_params": {"displayRequestDuration": "true"},
}

app.config.from_object("config.Config")
db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(home_bp)
app.register_blueprint(user_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(content_bp)

swagger = Swagger(
    app,
    decorators=[requires_basic_auth],
)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Uncaught exception",
        metadata={
            "exc_type": str(exc_type),
            "exc_value": str(exc_value),
            "exc_traceback": "".join(traceback.format_tb(exc_traceback)),
        },
    )


sys.excepthook = handle_exception

if __name__ == "__main__":
    download_nltk_resources()
    app.run(debug=True, port=5000, host="0.0.0.0")
