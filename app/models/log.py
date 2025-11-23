from database import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    feeder_id = db.Column(db.Integer, db.ForeignKey('feeders.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(32), nullable=False) # "auto" | "manual"
    duration_ms = db.Column(db.Integer, nullable=True)

    feeder = db.relationship('Feeder', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'feeder_id': self.feeder_id,
            'feeder_name': self.feeder.name,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'duration_ms': self.duration_ms
        }
