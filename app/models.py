import datetime

from app import db
from contracts.consts import MAX_DECIMAL


class RebaseHistory(db.Model):
    __tablename__ = 'rebase_history'

    id = db.Column(db.Integer, primary_key=True)
    usd_price = db.Column(db.Numeric(precision=MAX_DECIMAL))
    cpi_value = db.Column(db.Numeric(precision=MAX_DECIMAL))
    total_supply = db.Column(db.Numeric(precision=MAX_DECIMAL))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    raised = db.Column(db.Boolean)

    def serialize(self):
        repr_data = {
            'id': self.id,
            'usd_price': str(self.usd_price),
            'cpi_value': str(self.cpi_value),
            'total_supply': str(self.total_supply),
            'date': int(self.date.timestamp()),
            'raised': self.raised,
        }
        return repr_data


class LastRebase(db.Model):
    __tablename__ = 'last_rebase'

    id = db.Column(db.Integer, primary_key=True)
    seconds = db.Column(db.Integer)
