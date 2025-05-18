from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TimeField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class AppointmentForm(FlaskForm):
    counselor_id = SelectField('Counselor', coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Book Appointment')