import copy

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db

@dataclass
class MapsAnalysis(db.Model):
    __tablename__ = "maps_analysis"

    id: int
    address: str
    map_url: str
    name: str
    snippets: str
    website: str
    website_title: str
    website_backlinks: str
    website_keywords: str
    latitude: float
    longitude: float

    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    address = db.Column(db.Text, nullable=False)
    map_url = db.Column(db.Text, nullable=True)
    name = db.Column(db.Text, nullable=True)
    snippets = db.Column(db.Text, nullable=True)
    website = db.Column(db.Text, nullable=True)
    website_title = db.Column(db.Text, nullable=True)  # Fixed the typo
    website_backlinks = db.Column(db.Text, nullable=True)
    website_keywords = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)  # Changed to db.Float
    longitude = db.Column(db.Float, nullable=True)  # Changed to db.Float

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        obj_dict.pop("__table_args__", None)
        obj_dict["publish_date"] = (
            obj_dict.pop("publish_date").replace(tzinfo=timezone.utc).isoformat()
            if self.publish_date is not None
            else None
        )
        obj_dict["created_at"] = (
            obj_dict.pop("created_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["updated_at"] = (
            obj_dict.pop("updated_at").replace(tzinfo=timezone.utc).isoformat()
        )

        return obj_dict
