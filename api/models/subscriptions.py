import copy
from api.models.user import User
from api.models.subscription_type import SubscriptionType
from dataclasses import dataclass
from api.models import db
from datetime import datetime as dt, timezone
from api.assets import constants
import enum


class StatusEnums(str, enum.Enum):
    ISSUED = constants.UserSubscriptionStatus.ISSUED
    REVOKED = constants.UserSubscriptionStatus.REVOKED


@dataclass
class Subscription(db.Model):
    __tablename__ = "subscription"

    id: int
    user_id: int
    subscription_type_id: int
    started_on: dt
    valid_till: dt
    status: str
    invoice_link:str
    
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    subscription_type_id = db.Column(db.Integer, db.ForeignKey(SubscriptionType.id), nullable=False)
    started_on = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    valid_till = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(StatusEnums), default=StatusEnums.ISSUED, nullable=False)
    invoice_link = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    subscription_type = db.relationship("SubscriptionType", lazy=True)

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
        obj_dict["started_on"] = (
            obj_dict.pop("started_on").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["valid_till"] = (
            obj_dict.pop("valid_till").replace(tzinfo=timezone.utc).isoformat()
        )
        return obj_dict
