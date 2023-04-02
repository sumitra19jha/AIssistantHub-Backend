from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy(engine_options={"echo": Config.SQLALCHEMY_ECHO_DB_COMMANDS})