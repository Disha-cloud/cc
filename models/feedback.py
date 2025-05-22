from models import db  # Import db from the models package

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    feedback_type = db.Column(db.String(50))
    feedback_text = db.Column(db.Text)
    date_submitted = db.Column(db.DateTime)