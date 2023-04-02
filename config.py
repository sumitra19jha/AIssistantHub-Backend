from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))


class Config:
    # Database
    # SQLALCHEMY_DATABASE_URI = r"sqlite:///C:\Users\shiva\lg\db\backend.db"
    SQLALCHEMY_DATABASE_URI = "mysql://{}:{}@{}/{}".format(
        environ.get("MYSQL_USER"),
        environ.get("MYSQL_PASSWORD"),
        environ.get("MYSQL_HOST"),
        environ.get("MYSQL_DB"),
    )
    MYSQL_DB = environ.get("MYSQL_DB")
    YOUR_SEMRUSH_API_KEY = environ.get("YOUR_SEMRUSH_API_KEY")
    OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
    SQLALCHEMY_ECHO_DB_COMMANDS = bool(
        environ.get("SQLALCHEMY_ECHO_DB_COMMANDS", False)
    )

    # smtp configuration
    SMTP_USERNAME = environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = environ.get("SMTP_PASSWORD")
    SMTP_HOST = environ.get("SMTP_HOST")
    SMTP_PORT = environ.get("SMTP_PORT")
    SMTP_EMAIL_SENDER = environ.get("SMTP_EMAIL_SENDER")
    SMTP_EMAIL_SENDER_NAME = environ.get("SMTP_EMAIL_SENDER_NAME")