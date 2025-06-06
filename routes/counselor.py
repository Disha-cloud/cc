import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.document import Document
from models.appointment import Appointment
from models.message import Message
from models.activity import ActivityLog
from forms.document import DocumentForm
from forms.message import MessageForm
from utils.decorators import role_required

counselor = Blueprint('counselor', __name__)

@counselor.route('/dashboard')
@login_required
@role_required('counselor')
def dashboard():
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        counselor_id=current_user.id,
        status='confirmed'
    ).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.user_id,
        read_at=None
    ).count()
    
    return render_template(
        'counselor/dashboard.html',
        upcoming_appointments=upcoming_appointments,
        unread_messages=unread_messages
    )

@counselor.route('/documents', methods=['GET', 'POST'])
@login_required
@role_required('counselor')
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
                uploaded_by=current_user.id,
                is_public=True
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
            return redirect(url_for('counselor.documents'))
    
    # Public documents uploaded by counselors
    documents = Document.query.filter_by(is_public=True).all()
    
    return render_template('counselor/documents.html', form=form, documents=documents)

@counselor.route('/students')
@login_required
@role_required('counselor')
def students():
    # Get students who have appointments with this counselor
    appointments = Appointment.query.filter_by(counselor_id=current_user.id).all()
    student_ids = set([a.student_id for a in appointments])
    students = User.query.filter(User.id.in_(student_ids)).all()
    
    return render_template('counselor/students.html', students=students)

@counselor.route('/chat_list')
@login_required
@role_required('counselor')
def counsellor_chat_list():
    """Show list of student conversations for the counselor"""
    # Find all conversations for the current counselor
    sent_messages = Message.query.filter_by(sender_id=current_user.user_id).all()
    received_messages = Message.query.filter_by(receiver_id=current_user.user_id).all()
    
    # Get unique user ids from these messages
    user_ids = set()
    for msg in sent_messages:
        user_ids.add(msg.receiver_id)
    for msg in received_messages:
        user_ids.add(msg.sender_id)
        
    # Also add students assigned to this counselor who might not have messages yet
    assigned_students = User.query.filter_by(counselor_id=current_user.user_id, user_role='student').all()
    for student in assigned_students:
        user_ids.add(student.user_id)
        
    conversations = []
    for user_id in user_ids:
        other_user = User.query.get(user_id)
        if not other_user or other_user.user_role != 'student':
            continue
            
        # Get the last message
        last_message = Message.query.filter(
            ((Message.sender_id == current_user.user_id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user.user_id))
        ).order_by(Message.sent_at.desc()).first()
        
        # Count unread messages
        unread_count = Message.query.filter_by(
            sender_id=user_id,
            receiver_id=current_user.user_id,
            read_at=None
        ).count()
        
        # Add to conversations list
        conversations.append({
            'user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort by last message time, newest first
    conversations.sort(key=lambda x: x['last_message'].sent_at if x['last_message'] else datetime.min, reverse=True)
    
    return render_template('counsellor/chat_list.html', conversations=conversations)

@counselor.route('/send_message', methods=['POST'])
@login_required
@role_required('counselor')
def counsellor_send_message():
    """Send a new message as counselor"""
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    
    if not receiver_id or not content:
        flash('Invalid message data.', 'danger')
        return redirect(url_for('counselor.counsellor_chat_list'))
    
    # Create new message
    message = Message(
        sender_id=current_user.user_id,
        receiver_id=receiver_id,
        content=content,
        sent_at=datetime.utcnow()
    )
    
    db.session.add(message)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.user_id,
        action='Send Message',
        details=f'Sent message to student {receiver_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    # If this is AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'time': message.sent_at.strftime('%I:%M %p')
            }
        })
    
    # Otherwise redirect back to chat
    return redirect(url_for('auth.chat', user_id=receiver_id))

@counselor.route('/chat', methods=['GET', 'POST'])
@login_required
@role_required('counselor')
def chat():
    form = MessageForm()
    
    # Get students who have appointments with this counselor
    appointments = Appointment.query.filter_by(counselor_id=current_user.id).all()
    student_ids = set([a.student_id for a in appointments])
    students = User.query.filter(User.id.in_(student_ids)).all()
    
    form.receiver_id.choices = [(s.id, s.name) for s in students]
    
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=form.receiver_id.data,
            content=form.content.data,
            sent_at=datetime.utcnow()
        )
        
        db.session.add(message)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Send Message',
            details=f'Sent message to student {form.receiver_id.data}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('counselor.chat'))
    
    # Get student ID from query parameter if available
    student_id = request.args.get('student_id', None)
    if student_id:
        student = User.query.get(student_id)
        if student and student.id in student_ids:
            form.receiver_id.data = student.id
            
            # Get conversation with this student
            messages = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == student.id)) |
                ((Message.sender_id == student.id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.sent_at).all()
            
            # Mark unread messages as read
            unread_messages = Message.query.filter_by(
                sender_id=student.id,
                receiver_id=current_user.id,
                read_at=None
            ).all()
            
            for msg in unread_messages:
                msg.read_at = datetime.utcnow()
            
            db.session.commit()
            
            return render_template('counselor/chat.html', form=form, messages=messages, student=student)
    
    # If no student selected, show list of recent conversations
    recent_conversations = db.session.query(Message.sender_id, Message.receiver_id, 
                                         db.func.max(Message.sent_at).label('last_message'))\
        .filter((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id))\
        .group_by(Message.sender_id, Message.receiver_id)\
        .order_by(db.desc('last_message'))\
        .limit(10).all()
    
    conversations = []
    for conv in recent_conversations:
        other_id = conv.sender_id if conv.sender_id != current_user.id else conv.receiver_id
        other_user = User.query.get(other_id)
        if other_user and other_user.role == 'user':
            conversations.append({
                'user': other_user,
                'last_message': conv.last_message
            })
    
    return render_template('counselor/chat_list.html', conversations=conversations)

@counselor.route('/appointments')
@login_required
@role_required('counselor')
def appointments():
    appointments = Appointment.query.filter_by(counselor_id=current_user.id).all()
    return render_template('counselor/appointments.html', appointments=appointments)

@counselor.route('/appointment/<int:appointment_id>/update', methods=['POST'])
@login_required
@role_required('counselor')
def update_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.counselor_id != current_user.id:
        flash('You are not authorized to update this appointment.', 'danger')
        return redirect(url_for('counselor.appointments'))
    
    status = request.form.get('status')
    if status in ['confirmed', 'cancelled', 'completed']:
        appointment.status = status
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Update Appointment',
            details=f'Updated appointment {appointment.id} status to {status}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Appointment status updated to {status}.', 'success')
    
    return redirect(url_for('counselor.appointments'))