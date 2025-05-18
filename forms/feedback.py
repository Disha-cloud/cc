from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class FeedbackForm(FlaskForm):
    appointment_id = SelectField('Appointment', coerce=int, validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message='Rating must be between 1 and 5')
    ])
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Feedback')