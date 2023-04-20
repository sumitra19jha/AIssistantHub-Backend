import logging
from logging.config import dictConfig
import json
import os

from flask import request


with open("logging_config.json", "r") as file:
    logging.config.dictConfig(json.load(file))


class ContextualFilter(logging.Filter):
    def filter(self, log_record):
        log_record.url = ""
        log_record.method = ""
        log_record.ip = ""

        if hasattr(request, "path"):
            log_record.url = request.path
        if hasattr(request, "method"):
            log_record.method = request.method
        if hasattr(request, "environ"):
            log_record.ip = request.environ.get("REMOTE_ADDR", "")

        return True


class Logger:
    def __init__(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
        self.logger.addFilter(ContextualFilter())

    def log(self, level, message, metadata=None):

        json_string = ""
        if metadata is not None:
            try:
                json_string = json.dumps(metadata)
            except Exception as e:
                json_string = ""
                self.logger.exception("Error while logging metadata")

            metadata_conc_message = str(message) + " - " + json_string
        else:
            metadata_conc_message = str(message)

        self.logger.log(getattr(logging, level), metadata_conc_message)

    # Lean methods
    def debug(self, message, metadata=None):
        self.log("DEBUG", message, metadata)

    def info(self, message, metadata=None):
        self.log("INFO", message, metadata)

    def error(self, message, metadata=None):
        self.log("ERROR", message, metadata)

    # It is preferred to use the following in exception handling instead of above.

    def exception(self, message):
        self.logger.exception(message)
