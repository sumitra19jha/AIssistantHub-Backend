import copy

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db

@dataclass
class NewsAnalysis(db.Model):
    __tablename__ = "news_analysis"

    id: int
    title: str
    html_title: str
    display_link: str
    formatted_url: str
    snippet: str

    kind: str
    link: str
    pagemap: object
    
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    html_title = db.Column(db.Text, nullable=True)
    display_link = db.Column(db.Text, nullable=True)
    formatted_url = db.Column(db.Text, nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    kind = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(255), unique=True, nullable=True)

    pagemap = db.Column(db.JSON, nullable=True)

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
