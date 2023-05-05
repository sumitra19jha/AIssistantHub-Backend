import copy
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db
from api.models.youtube_search_query import YouTubeSearchQuery
from api.models.youtube_video_analysis import YouTubeVideoAnalysis


@dataclass
class YouTubeSearchVideoRel(db.Model):
    __tablename__ = "youtube_search_video_rel"

    id: int
    youtube_search_query_id: int
    youtube_video_analysis_id: int
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    youtube_search_query_id = db.Column(db.Integer, db.ForeignKey(YouTubeSearchQuery.id), nullable=False)
    youtube_video_analysis_id = db.Column(db.Integer, db.ForeignKey(YouTubeVideoAnalysis.id), nullable=False)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    youtube_search_query = db.relationship(YouTubeSearchQuery, backref="youtube_search_video_rel", lazy=True)
    youtube_video_analysis = db.relationship(YouTubeVideoAnalysis, backref="youtube_search_video_rel", lazy=True)

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
