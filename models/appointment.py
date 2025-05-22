from datetime import datetime
from models import db

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    counselor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    appointment_date = db.Column(db.Date)
    appointment_time = db.Column(db.Time)
    topic = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)