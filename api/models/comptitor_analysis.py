import copy

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db

@dataclass
class CompetitorAnalysis(db.Model):
    __tablename__ = "comptitor_analysis"

    id: int
    link: str
    title: str
    meta_description: str

    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    link = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        obj_dict.pop("__table_args__", None)
        obj_dict["created_at"] = (
            obj_dict.pop("created_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["updated_at"] = (
            obj_dict.pop("updated_at").replace(tzinfo=timezone.utc).isoformat()
        )

        return obj_dict
