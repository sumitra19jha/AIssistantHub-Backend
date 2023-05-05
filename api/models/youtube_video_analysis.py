import copy

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db

@dataclass
class YouTubeVideoAnalysis(db.Model):
    __tablename__ = "youtube_video_analysis"

    id: int
    title: str
    description: str
    video_id: str
    video_url: str
    channel_title: str
    publish_date: dt
    thumbnail_url: str
    views: int
    likes_count: int
    comments_count: int
    video_duration: int
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_id = db.Column(db.String(100), unique=True, nullable=False)
    video_url = db.Column(db.Text, nullable=False)
    channel_title = db.Column(db.Text, nullable=True)
    publish_date = db.Column(db.DateTime, nullable=True)
    thumbnail_url = db.Column(db.Text, nullable=True)
    views = db.Column(db.Integer, nullable=True)
    likes_count = db.Column(db.Integer, nullable=True)
    comments_count = db.Column(db.Integer, nullable=True)
    video_duration = db.Column(db.Integer, nullable=True)

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
