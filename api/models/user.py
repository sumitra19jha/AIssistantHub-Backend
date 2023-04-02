import copy
import enum
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.assets import constants
from api.models import db


class UserStatusEnums(str, enum.Enum):
    active = constants.UserCons.enum_status_active
    email_verification_pending = constants.UserCons.enum_status_email_verification_pending
    phone_verification_pending = constants.UserCons.enum_status_phone_verification_pending
    deleted = constants.UserCons.enum_status_deleted


class UserGenderEnums(str, enum.Enum):
    male = constants.UserCons.enum_gender_male
    female = constants.UserCons.enum_gender_female


@dataclass
class User(db.Model):
    __tablename__ = "users"
    """
    Note; Any new field added here should be added to CachedUser model below.
    And CachedUser values from redis needs to be cleared.
    """
    id: int
    name: str
    email: str
    phone_country_code: str
    phone_number: str
    oauth_id_google: str
    oauth_id_facebook: str
    oauth_id_apple: str
    status: str
    profile_photo_url: str
    created_at: dt
    updated_at: dt
    
    dob: dt = db.Column(db.DateTime)
    gender: str = db.Column(db.Enum(UserGenderEnums))
    city: str = db.Column(db.String(500))
    country: str = db.Column(db.String(500))
    about_me: str = db.Column(db.Text)

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String(300))
    password = db.Column(db.Text)
    status = db.Column(db.Enum(UserStatusEnums), nullable=False)
    profile_photo_url = db.Column(db.Text)
    email = db.Column(db.String(150), unique=True, nullable=True)
    phone_country_code = db.Column(db.String(20), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    
    oauth_id_google = db.Column(db.String(200), unique=True, nullable=True)
    oauth_id_facebook = db.Column(db.String(200), unique=True, nullable=True)
    oauth_id_apple = db.Column(db.String(200), unique=True, nullable=True)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False
    )

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        obj_dict.pop("__table_args__", None)
        obj_dict.pop("password", None)
        obj_dict["dob"] = (
            obj_dict.pop("dob").date().isoformat() if self.dob is not None else None
        )
        obj_dict["created_at"] = (
            obj_dict.pop("created_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["updated_at"] = (
            obj_dict.pop("updated_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["has_set_password"] = self.password is not None

        return obj_dict