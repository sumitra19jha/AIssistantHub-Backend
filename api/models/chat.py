import copy
from api.models.user import User
from api.models.content import Content
from dataclasses import dataclass
from api.models import db
from datetime import datetime as dt, timezone
from api.assets import constants
import enum

class ChatTypeEnums(str, enum.Enum):
    USER=constants.ChatTypes.USER
    AI=constants.ChatTypes.AI

@dataclass
class Chat(db.Model):
    __tablename__ = "chat"

    id: int
    content_id:int
    user_id: int
    type: str
    message:str
    
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    content_id = db.Column(db.Integer, db.ForeignKey(Content.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    type = db.Column(db.Enum(ChatTypeEnums), default=ChatTypeEnums.USER, nullable=False)
    message=db.Column(db.Text, nullable=False)

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
