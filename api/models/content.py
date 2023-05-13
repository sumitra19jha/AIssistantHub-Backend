import copy
from api.models.user import User
from dataclasses import dataclass
from api.models import db
from datetime import datetime as dt, timezone
from api.assets import constants
import enum


class ContentStatusEnums(str, enum.Enum):
    SUCCESS = constants.ContentStatus.SUCCESS
    ERROR = constants.ContentStatus.ERROR

class ContentTypeEnums(str, enum.Enum):
    SOCIAL_MEDIA_POST=constants.ContentTypes.SOCIAL_MEDIA_POST
    BLOG_POST=constants.ContentTypes.BLOG_POST
    ARTICLE=constants.ContentTypes.ARTICLE
    EMAIL_MARKETING=constants.ContentTypes.EMAIL_MARKETING
    NEWS_LETTER=constants.ContentTypes.NEWS_LETTER
    PRODUCT_DESCRIPTION=constants.ContentTypes.PRODUCT_DESCRIPTION
    CASE_STUDY=constants.ContentTypes.CASE_STUDY
    WHITE_PAPER=constants.ContentTypes.WHITE_PAPER
    LISTICLE=constants.ContentTypes.LISTICLE
    VIDEO_SCRIPT=constants.ContentTypes.VIDEO_SCRIPT
    WEBINAR_SCRIPT=constants.ContentTypes.WEBINAR_SCRIPT
    EDUCATIONAL_CONTENT=constants.ContentTypes.EDUCATIONAL_CONTENT

class ContentLengthEnums(str, enum.Enum):
    SHORT = constants.ContentLengths.SHORT
    MEDIUM = constants.ContentLengths.MEDIUM
    LONG = constants.ContentLengths.LONG

@dataclass
class Content(db.Model):
    __tablename__ = "content"

    id: int
    user_id: int
    type: str
    topic:str
    keywords:str
    length:str
    status: str
    urls: object

    platform:str
    purpose:str
    system_message:str
    user_message:str
    model:str
    model_response:str
    content_data:str
    no_of_prompt_tokens:int
    no_of_completion_tokens:int
    finish_reason:str
    
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    type = db.Column(db.Enum(ContentTypeEnums), default=ContentTypeEnums.BLOG_POST, nullable=False)
    topic=db.Column(db.Text, nullable=False)
    keywords=db.Column(db.Text, nullable=True)
    urls=db.Column(db.JSON, nullable=True)
    length=db.Column(db.Enum(ContentLengthEnums), default=ContentLengthEnums.SHORT, nullable=False)
    status = db.Column(db.Enum(ContentStatusEnums), nullable=True)

    platform=db.Column(db.String(255), nullable=True)
    purpose=db.Column(db.String(255), nullable=True)
    system_message=db.Column(db.Text, nullable=True)
    user_message=db.Column(db.Text, nullable=True)
    model=db.Column(db.String(255), nullable=True)
    model_response=db.Column(db.Text, nullable=True)
    content_data=db.Column(db.Text, nullable=True)
    no_of_prompt_tokens = db.Column(db.Integer, nullable=True)
    no_of_completion_tokens = db.Column(db.Integer, nullable=True)
    finish_reason=db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        obj_dict["created_at"] = (
            obj_dict.pop("created_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["updated_at"] = (
            obj_dict.pop("updated_at").replace(tzinfo=timezone.utc).isoformat()
        )
        return obj_dict
