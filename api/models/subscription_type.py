import copy
import enum
from dataclasses import dataclass

from api.assets import constants
from api.models import db


class SubscriptionTypesEnums(str, enum.Enum):
    TRIAL = constants.SubscriptionTypes.TRIAL
    STARTER = constants.SubscriptionTypes.STARTER
    PRO = constants.SubscriptionTypes.PRO
    ENTERPRISE = constants.SubscriptionTypes.ENTERPRISE


@dataclass
class SubscriptionType(db.Model):
    __tablename__ = "subscription_type"

    id: int
    subscription_type: str
    subscription_name: str
    subscription_price: float
    description: str
    access_control: str

    id = db.Column(db.Integer, primary_key=False, unique=True, nullable=False)
    subscription_type = db.Column(db.Enum(SubscriptionTypesEnums), primary_key=True, nullable=False)
    subscription_name = db.Column(db.String(255))
    subscription_price = db.Column(db.Float)
    description = db.Column(db.Text)
    access_control = db.Column(db.Text)

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        return obj_dict