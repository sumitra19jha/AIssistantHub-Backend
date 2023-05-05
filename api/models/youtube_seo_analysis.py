import copy

from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timezone

from api.models import db
from api.models.user import User


@dataclass
class YouTubeSEOAnalysis(db.Model):
    __tablename__ = "youtube_seo_analysis"
    
    id: int
    user_id: int
    business_type: str
    target_audience: str
    industry: str
    goals: str
    country: str
    user_ip: str
    suggestions: object
    created_at: dt
    updated_at: dt
    
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    target_audience = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    goals = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    user_ip = db.Column(db.String(50), nullable=True)
    suggestions = db.Column(db.JSON, nullable=True)
    
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
