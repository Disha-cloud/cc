from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db  # Make sure this points to your initialized SQLAlchemy instance

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    education_level = db.Column(db.String(100), nullable=True)
    interests = db.Column(db.String(255), nullable=True)  # stored as comma-separated string
    counselor_id = db.Column(db.Integer, nullable=True)

    password_hash = db.Column(db.String(128), nullable=False)
    user_role = db.Column(db.String(20), nullable=False, default='student')
    course = db.Column(db.String(100), nullable=True)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    @property
    def is_online(self):
        """Check if user was online in the last 5 minutes"""
        if not self.last_login:
            return False
        
        return (datetime.utcnow() - self.last_login).total_seconds() < 300  # 5 minutes
    
   
    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.user_role == 'admin'

    def is_counsellor(self):
        return self.user_role == 'counsellor'

    def is_student(self):
        return self.user_role == 'student'

    def __repr__(self):
        return f"<User {self.email} - {self.user_role}>"
    
class CareerCounselor(db.Model):
    __tablename__ = 'CareerCounselors'
    counsellor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.Text)
    years_of_experience = db.Column(db.Integer)
    bio = db.Column(db.Text)
    availability_status = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Numeric(3, 2), default=0.0)