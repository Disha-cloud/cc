# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # existing fields...
    # Ensure all required fields like first_name, email, etc. are already defined

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    counsellor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.Time)
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled', 'rescheduled'), default='scheduled')
    mode = db.Column(db.Enum('online', 'offline', 'phone'), nullable=False)
    meeting_link = db.Column(db.String(255))
    location = db.Column(db.String(255))
    is_free = db.Column(db.Boolean, default=False)
    fee = db.Column(db.Numeric(10, 2))
    payment_status = db.Column(db.Enum('paid', 'pending', 'not_required'), default='not_required')
   

