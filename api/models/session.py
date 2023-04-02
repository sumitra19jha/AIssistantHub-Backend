import enum
import hashlib
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta

from api.assets import params
from api.assets.constants import SessionCons
from api.models import db
from api.models.user import User


class SessionStatusEnums(str, enum.Enum):
    active = SessionCons.enum_active
    logged_out = SessionCons.enum_logged_out


class SessionLoginMethodEnums(str, enum.Enum):
    name = SessionCons.enum_login_method_name
    email = SessionCons.enum_login_method_email
    phone = SessionCons.enum_login_method_phone
    google = SessionCons.enum_login_method_google
    facebook = SessionCons.enum_login_method_facebook
    apple = SessionCons.enum_login_method_apple


@dataclass
class Session(db.Model):
    __tablename__ = "session"
    id: int
    user_id: int
    session_id: int
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    session_id = db.Column(
        db.String(500),
        nullable=False,
        unique=True,
        default=lambda u=user_id: hashlib.md5(
            "-".join([str(u), str(dt.utcnow().timestamp())]).encode("utf-8")
        ).hexdigest(),
    )
    status = db.Column(
        db.Enum(SessionStatusEnums), default=SessionCons.enum_active, nullable=False
    )
    valid_till = db.Column(
        db.DateTime,
        default=lambda: dt.utcnow()
        + timedelta(days=params.default_session_timeout_days),
        nullable=False,
    )
    timezone = db.Column(db.String(100))
    ip_address = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_os_version = db.Column(db.String(100))
    app_version = db.Column(db.String(50))
    device_details = db.Column(db.Text)
    login_method = db.Column(
        db.Enum(SessionLoginMethodEnums),
    )
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False
    )

    user = db.relationship("User", lazy=True)
