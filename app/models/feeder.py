from database import db
from datetime import datetime
import secrets

class Feeder(db.Model):
    __tablename__ = 'feeders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    interval_seconds = db.Column(db.Integer, default=3600) # Default 1 hour
    open_duration_ms = db.Column(db.Integer, default=1000) # Default 1 second
    next_run = db.Column(db.DateTime, nullable=True)
    last_run = db.Column(db.DateTime, nullable=True)
    online = db.Column(db.Boolean, default=False)
    battery_level = db.Column(db.Integer, default=100)
    token = db.Column(db.String(64), unique=True, nullable=False)
    firmware_version = db.Column(db.String(32), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    food_tank_id = db.Column(db.Integer, db.ForeignKey('tanks.id'), nullable=True)
    food_tank = db.relationship('Tank', foreign_keys=[food_tank_id], backref=db.backref('food_feeders', lazy=True))
    
    water_tank_id = db.Column(db.Integer, db.ForeignKey('tanks.id'), nullable=True)
    water_tank = db.relationship('Tank', foreign_keys=[water_tank_id], backref=db.backref('water_feeders', lazy=True))

    avatar = db.Column(db.String(50), default='cat') # cat, dog, mouse, etc.
    mode = db.Column(db.String(20), default='interval') # interval, schedule
    schedule_times = db.Column(db.String(256), default='[]') # JSON string of times ["08:00", "18:00"]
    is_locked = db.Column(db.Boolean, default=False) # Safety lock

    # Sensor & Scale Logic (Food)
    drawer_weight = db.Column(db.Float, default=0.0) # Current weight in drawer (g)
    target_weight = db.Column(db.Float, default=210.0) # Target weight (g) per unit (Full)
    warning_weight = db.Column(db.Float, default=80.0) # LSL Threshold
    critical_weight = db.Column(db.Float, default=20.0) # LSLL Threshold
    dose_count = db.Column(db.Integer, default=1) # How many units to dispense per cycle
    sensor_state = db.Column(db.String(16), default='LSH') # Food Sensor: LSH, LSL, LSLL
    
    # Water Logic
    water_locked = db.Column(db.Boolean, default=False) # Safety lock for water solenoid
    water_sensor_state = db.Column(db.String(16), default='LSH') # Water Sub-tank Sensor: LSH, LSLL
    
    status = db.Column(db.String(16), default='NORMAL') # NORMAL, WARNING, CRITICAL, TRIP
    trip_reason = db.Column(db.String(128), nullable=True) # Reason for TRIP
    
    # Block & Water Logic
    block_name = db.Column(db.String(64), nullable=True) # Grouping (e.g., "Block A")
    water_mode = db.Column(db.String(16), default='AUTO') # AUTO, MANUAL
    water_valve_state = db.Column(db.String(16), default='CLOSED') # OPEN, CLOSED

    def __init__(self, name, food_tank_id=None, water_tank_id=None, avatar='cat'):
        self.name = name
        self.food_tank_id = food_tank_id
        self.water_tank_id = water_tank_id
        self.avatar = avatar
        self.token = secrets.token_urlsafe(32)
        self.last_seen = datetime.utcnow()
        self.battery_level = 100
        self.target_weight = 210.0
        self.warning_weight = 80.0
        self.critical_weight = 20.0
        self.dose_count = 1
        self.sensor_state = 'LSH'
        self.water_sensor_state = 'LSH'
        self.status = 'NORMAL'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'interval_seconds': self.interval_seconds,
            'open_duration_ms': self.open_duration_ms,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'online': self.online,
            'battery_level': self.battery_level,
            'firmware_version': self.firmware_version,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'food_tank_id': self.food_tank_id,
            'water_tank_id': self.water_tank_id,
            'avatar': self.avatar,
            'mode': self.mode,
            'schedule_times': self.schedule_times,
            'is_locked': self.is_locked,
            'drawer_weight': self.drawer_weight,
            'target_weight': self.target_weight,
            'warning_weight': self.warning_weight,
            'critical_weight': self.critical_weight,
            'dose_count': self.dose_count,
            'sensor_state': self.sensor_state,
            'water_locked': self.water_locked,
            'water_sensor_state': self.water_sensor_state,
            'status': self.status,
            'trip_reason': self.trip_reason
        }
