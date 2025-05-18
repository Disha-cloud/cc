from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class MessageForm(FlaskForm):
    receiver_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    content = TextAreaField('Message', validators=[
        DataRequired(),
        Length(max=1000, message='Message cannot exceed 1000 characters')
    ])
    submit = SubmitField('Send Message')