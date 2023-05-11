import copy
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db
from api.models.news_analysis import NewsAnalysis
from api.models.search_query import SearchQuery


@dataclass
class NewsSearchRel(db.Model):
    __tablename__ = "news_search_rel"

    id: int
    search_query_id: int
    news_analysis_id: int
    
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    search_query_id = db.Column(db.Integer, db.ForeignKey(SearchQuery.id), nullable=False)
    news_analysis_id = db.Column(db.Integer, db.ForeignKey(NewsAnalysis.id), nullable=False)

    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    search_query = db.relationship(SearchQuery, backref="news_search_rel", lazy=True)
    news_analysis = db.relationship(NewsAnalysis, backref="news_search_rel", lazy=True)

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