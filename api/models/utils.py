from datetime import datetime as dt
from api.models import db


class BaseModelParent(db.Model):
    __abstract__ = True
    created_at: dt
    updated_at: dt

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False
    )


class BaseModelIdNotPrimary(BaseModelParent):
    __abstract__ = True
    id: int
    id = db.Column(db.Integer, primary_key=False, unique=True, nullable=False)


class BaseModel(BaseModelParent):
    __abstract__ = True
    id: int
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)


class BaseModelIdNotPrimaryNoTimestamps(db.Model):
    __abstract__ = True
    id: int
    id = db.Column(db.Integer, primary_key=False, unique=True, nullable=False)
