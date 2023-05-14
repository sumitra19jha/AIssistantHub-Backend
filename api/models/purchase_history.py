import copy
from api.models.user import User
from dataclasses import dataclass
from api.models import db
from datetime import datetime as dt, timezone
from api.models.purchase import Purchase


@dataclass
class PurchaseHistory(db.Model):
    __tablename__ = "purchase_history"

    id: int
    purchase_id: int
    amount: float
    created_at: dt
    updated_at: dt

    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey(Purchase.id), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow, default=dt.utcnow, nullable=False)

    purchase = db.relationship("Purchase", lazy=True)

    def to_dict(self):
        assert self.id is not None
        obj_dict = copy.deepcopy(self.__dict__)
        obj_dict.pop("_sa_instance_state", None)
        obj_dict["created_at"] = (
            obj_dict.pop("created_at").replace(tzinfo=timezone.utc).isoformat()
        )
        obj_dict["updated_at"] = (
            obj_dict.pop("updated_at").replace(tzinfo=timezone.utc).isoformat()
        )
        return obj_dict