from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

from models.user import User
from models.document import Document
from models.appointment import Appointment
from models.feedback import Feedback
from models.message import Message
from models.activity import ActivityLog