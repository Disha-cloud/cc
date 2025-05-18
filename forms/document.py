from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class DocumentForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired(), Length(max=100)])
    document = FileField('Upload Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'png'], 'Only PDF, Word, Text, and Image files are allowed!')
    ])
    description = TextAreaField('Description', validators=[Length(max=500)])
    is_public = BooleanField('Make Public')
    submit = SubmitField('Upload')