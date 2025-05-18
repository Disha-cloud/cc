from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class UserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[
        ('user', 'Student'),
        ('counselor', 'Counselor'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=20)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    course = StringField('Course', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Save')