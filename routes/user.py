import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.document import Document
from models.appointment import Appointment
from models.feedback import Feedback
from models.activity import ActivityLog
from forms.document import DocumentForm
from forms.appointment import AppointmentForm
from forms.feedback import FeedbackForm
from utils.decorators import role_required

user = Blueprint('user', __name__)

@user.route('/dashboard')
@login_required
@role_required('user')
def dashboard():
    return render_template('user/dashboard.html')

@user.route('/documents', methods=['GET', 'POST'])
@login_required
@role_required('user')
def documents():
    form = DocumentForm()
    
    if form.validate_on_submit():
        file = form.document.data
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOADED_DOCUMENTS_DEST'], filename)
            file.save(file_path)
            
            document = Document(
                title=form.title.data,
                filename=filename,
                file_path=file_path,
                description=form.description.data,
                user_id=current_user.id,
                uploaded_by=current_user.id
            )
            
            db.session.add(document)
            
            # Log activity
            log = ActivityLog(
                user_id=current_user.id,
                action='Upload Document',
                details=f'Uploaded document: {form.title.data}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('user.documents'))
    
    documents = Document.query.filter_by(user_id=current_user.id).all()
    
    return render_template('user/documents.html', form=form, documents=documents)

@user.route('/appointments', methods=['GET', 'POST'])
@login_required
@role_required('user')
def appointments():
    form = AppointmentForm()
    
    # Get counselors for dropdown
    counselors = User.query.filter_by(role='counselor').all()
    form.counselor_id.choices = [(c.id, c.name) for c in counselors]
    
    if form.validate_on_submit():
        appointment = Appointment(
            student_id=current_user.id,
            counselor_id=form.counselor_id.data,
            date=form.date.data,
            time=form.time.data,
            notes=form.notes.data
        )
        
        db.session.add(appointment)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Book Appointment',
            details=f'Booked appointment with counselor {form.counselor_id.data} on {form.date.data}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('user.appointments'))
    
    appointments = Appointment.query.filter_by(student_id=current_user.id).all()
    
    return render_template('user/appointments.html', form=form, appointments=appointments)

@user.route('/feedback', methods=['GET', 'POST'])
@login_required
@role_required('user')
def feedback():
    form = FeedbackForm()
    
    # Get appointments for dropdown
    appointments = Appointment.query.filter_by(
        student_id=current_user.id, 
        status='completed'
    ).all()
    
    form.appointment_id.choices = [(a.id, f'{a.counselor.name} - {a.date}') for a in appointments]
    
    if form.validate_on_submit():
        appointment = Appointment.query.get(form.appointment_id.data)
        
        feedback = Feedback(
            student_id=current_user.id,
            counselor_id=appointment.counselor_id,
            appointment_id=form.appointment_id.data,
            rating=form.rating.data,
            comments=form.comments.data
        )
        
        db.session.add(feedback)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Submit Feedback',
            details=f'Submitted feedback for appointment {form.appointment_id.data}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('user.feedback'))
    
    feedbacks = Feedback.query.filter_by(student_id=current_user.id).all()
    
    return render_template('user/feedback.html', form=form, feedbacks=feedbacks)