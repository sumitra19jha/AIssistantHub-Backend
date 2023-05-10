import copy
import enum

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.assets import constants
from api.models import db


class ProjectTypeEnums(str, enum.Enum):
    youtube = constants.ProjectTypeCons.enum_youtube
    news = constants.ProjectTypeCons.enum_news
    maps = constants.ProjectTypeCons.enum_maps
    google_search = constants.ProjectTypeCons.enum_google_search
    reddit = constants.ProjectTypeCons.enum_reddit
    competitor = constants.ProjectTypeCons.enum_competitor



@dataclass
class Analysis(db.Model):
    __tablename__ = "analysis"

    id: int
    type: str
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
    display_link: str
    formatted_url: str
    html_formatted_url: str
    html_snippet: str
    html_title: str
    kind: str
    link: str
    pagemap: object
    snippet: str
    address: str
    map_url: str
    name: str
    website: str
    backlinks: str
    keywords: str
    latitude: float
    longitude: float

    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    type = db.Column(db.Enum(ProjectTypeEnums), nullable=False)
    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    video_id = db.Column(db.String(100), unique=True, nullable=True)
    video_url = db.Column(db.Text, nullable=True)
    channel_title = db.Column(db.Text, nullable=True)
    publish_date = db.Column(db.DateTime, nullable=True)
    thumbnail_url = db.Column(db.Text, nullable=True)
    views = db.Column(db.Integer, nullable=True)
    likes_count = db.Column(db.Integer, nullable=True)
    comments_count = db.Column(db.Integer, nullable=True)
    video_duration = db.Column(db.Integer, nullable=True)
    display_link = db.Column(db.String(255), nullable=True)
    formatted_url = db.Column(db.Text, nullable=True)
    html_formatted_url = db.Column(db.Text, nullable=True)
    html_snippet = db.Column(db.Text, nullable=True)
    html_title = db.Column(db.Text, nullable=True)
    kind = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=True)
    pagemap = db.Column(db.JSON, nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    map_url = db.Column(db.Text, nullable=True)
    name = db.Column(db.Text, nullable=True)
    website = db.Column(db.Text, nullable=True)
    backlinks = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

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