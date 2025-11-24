from database import db
from datetime import datetime

class Tank(db.Model):
    __tablename__ = 'tanks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), nullable=False) # 'water' or 'food'
    level = db.Column(db.Integer, default=100) # 0-100% (Calculated or manual)
    capacity = db.Column(db.String(32), nullable=True) # e.g. "5L", "2kg" (Display only)
    current_weight = db.Column(db.Float, default=0.0) # Current weight in kg/L
    max_weight = db.Column(db.Float, default=5.0) # Max capacity in kg/L
    
    # Device Connectivity
    token = db.Column(db.String(64), unique=True, nullable=True)
    online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    last_refill = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Block Logic
    block_name = db.Column(db.String(64), nullable=True)

    def __init__(self, **kwargs):
        super(Tank, self).__init__(**kwargs)
        if not self.token:
            self.token = self.generate_token()

    def generate_token(self):
        import secrets
        return secrets.token_urlsafe(32)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'level': self.level,
            'capacity': self.capacity,
            'online': self.online,
            'last_refill': self.last_refill.isoformat() if self.last_refill else None,
            'block_name': self.block_name
        }
