import copy
import enum
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.assets import constants
from api.models import db
from api.models.seo_project import SEOProject

class ProjectTypeEnums(str, enum.Enum):
    youtube = constants.ProjectTypeCons.enum_youtube
    news = constants.ProjectTypeCons.enum_news
    maps = constants.ProjectTypeCons.enum_maps
    google_search = constants.ProjectTypeCons.enum_google_search
    reddit = constants.ProjectTypeCons.enum_reddit
    competitor = constants.ProjectTypeCons.enum_competitor

@dataclass
class SearchQuery(db.Model):
    __tablename__ = "search_query"

    id: int
    type:str
    search_query: str
    seo_project_id: int

    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    type = db.Column(db.Enum(ProjectTypeEnums), nullable=False)
    search_query = db.Column(db.Text, nullable=False)
    seo_project_id = db.Column(db.Integer, db.ForeignKey(SEOProject.id), nullable=False)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    seo_project = db.relationship(SEOProject, backref="search_query", lazy=True)

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