import copy
import enum
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.assets import constants
from api.models import db
from api.models.youtube_seo_analysis import YouTubeSEOAnalysis


@dataclass
class YouTubeSearchQuery(db.Model):
    __tablename__ = "youtube_search_query"
    
    id: int
    search_query: str
    youtube_seo_analysis_id: int

    created_at: dt
    updated_at: dt
    
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    search_query = db.Column(db.Text, nullable=False)
    youtube_seo_analysis_id = db.Column(db.Integer, db.ForeignKey(YouTubeSEOAnalysis.id), nullable=False)
    
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    youtube_seo_analysis = db.relationship(YouTubeSEOAnalysis, backref="youtube_search_query", lazy=True)

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