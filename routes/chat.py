import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.message import Message, ChatRoom
from models.activity import ActivityLog

chat = Blueprint('chat', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat.route('/chat')
@login_required
def chat_home():
    """Main chat interface"""
    if current_user.user_role == 'student':
        # Get student's assigned counselor
        counselor = User.query.get(current_user.counselor_id) if current_user.counselor_id else None
        if not counselor:
            return render_template('chat/no_counselor.html')
        
        chat_partner = counselor
        chat_room = ChatRoom.get_or_create(current_user.user_id, counselor.user_id)
        
    elif current_user.user_role == 'counsellor':
        # Get chat partner from URL parameter or show list
        partner_id = request.args.get('partner_id')
        if not partner_id:
            return render_template('chat/counselor_chat_list.html')
        
        chat_partner = User.query.get(partner_id)
        if not chat_partner or chat_partner.user_role != 'student':
            return render_template('chat/invalid_partner.html')
        
        # Check if this student is assigned to this counselor
        if chat_partner.counselor_id != current_user.user_id:
            return render_template('chat/unauthorized_chat.html')
        
        chat_room = ChatRoom.get_or_create(chat_partner.user_id, current_user.user_id)
        
    else:
        return render_template('chat/unauthorized.html')
    
    # Get chat messages
    messages = Message.query.filter(
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == chat_partner.user_id)) |
        ((Message.sender_id == chat_partner.user_id) & (Message.receiver_id == current_user.user_id))
    ).filter_by(is_deleted=False).order_by(Message.sent_at).all()
    
    # Mark messages as read
    unread_messages = Message.query.filter_by(
        sender_id=chat_partner.user_id,
        receiver_id=current_user.user_id,
        read_at=None
    ).all()
    
    for msg in unread_messages:
        msg.mark_as_read()
    
    return render_template('chat/chat_room.html', 
                         chat_partner=chat_partner, 
                         messages=messages,
                         chat_room=chat_room)

@chat.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    """Send a message via API"""
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        
        if not receiver_id or not content:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Validate chat permissions
        if current_user.user_role == 'student':
            if receiver.user_id != current_user.counselor_id:
                return jsonify({'success': False, 'error': 'Unauthorized chat'}), 403
        elif current_user.user_role == 'counsellor':
            if receiver.counselor_id != current_user.user_id:
                return jsonify({'success': False, 'error': 'Unauthorized chat'}), 403
        
        # Create message
        message = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            content=content,
            message_type='text'
        )
        
        db.session.add(message)
        
        # Update chat room activity
        if current_user.user_role == 'student':
            chat_room = ChatRoom.get_or_create(current_user.user_id, receiver_id)
        else:
            chat_room = ChatRoom.get_or_create(receiver_id, current_user.user_id)
        
        chat_room.update_activity()
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.user_id,
            action='Send Message',
            details=f'Sent message to {receiver.first_name} {receiver.last_name or ""}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@chat.route('/api/get_messages')
@login_required
def get_messages():
    """Get messages for current chat"""
    partner_id = request.args.get('partner_id')
    last_message_id = request.args.get('last_message_id', 0, type=int)
    
    if not partner_id:
        return jsonify({'success': False, 'error': 'Partner ID required'}), 400
    
    partner = User.query.get(partner_id)
    if not partner:
        return jsonify({'success': False, 'error': 'Partner not found'}), 404
    
    # Validate chat permissions
    if current_user.user_role == 'student':
        if partner.user_id != current_user.counselor_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    elif current_user.user_role == 'counsellor':
        if partner.counselor_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Get new messages
    messages = Message.query.filter(
        Message.id > last_message_id,
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == partner_id)) |
        ((Message.sender_id == partner_id) & (Message.receiver_id == current_user.user_id))
    ).filter_by(is_deleted=False).order_by(Message.sent_at).all()
    
    # Mark new messages from partner as read
    unread_messages = [m for m in messages if m.sender_id == int(partner_id) and not m.read_at]
    for msg in unread_messages:
        msg.mark_as_read()
    
    return jsonify({
        'success': True,
        'messages': [msg.to_dict() for msg in messages]
    })

@chat.route('/api/upload_file', methods=['POST'])
@login_required
def upload_file():
    """Upload file in chat"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        receiver_id = request.form.get('receiver_id')
        
        if not receiver_id:
            return jsonify({'success': False, 'error': 'Receiver ID required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Validate chat permissions (same as send_message)
        if current_user.user_role == 'student':
            if receiver.user_id != current_user.counselor_id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        elif current_user.user_role == 'counsellor':
            if receiver.counselor_id != current_user.user_id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'chat_files')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Create message with file
        message = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            content=f"Shared file: {file.filename}",
            message_type='file',
            file_path=f"chat_files/{filename}"
        )
        
        db.session.add(message)
        
        # Update chat room activity
        if current_user.user_role == 'student':
            chat_room = ChatRoom.get_or_create(current_user.user_id, receiver_id)
        else:
            chat_room = ChatRoom.get_or_create(receiver_id, current_user.user_id)
        
        chat_room.update_activity()
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.user_id,
            action='Upload File',
            details=f'Uploaded file {file.filename} to chat with {receiver.first_name}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@chat.route('/counselor/students')
@login_required
def counselor_students():
    """Get list of students for counselor to chat with"""
    if current_user.user_role != 'counsellor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get students assigned to this counselor
    students = User.query.filter_by(
        counselor_id=current_user.user_id,
        user_role='student'
    ).all()
    
    student_data = []
    for student in students:
        # Get last message
        last_message = Message.query.filter(
            ((Message.sender_id == current_user.user_id) & (Message.receiver_id == student.user_id)) |
            ((Message.sender_id == student.user_id) & (Message.receiver_id == current_user.user_id))
        ).order_by(Message.sent_at.desc()).first()
        
        # Get unread count
        unread_count = Message.query.filter_by(
            sender_id=student.user_id,
            receiver_id=current_user.user_id,
            read_at=None
        ).count()
        
        student_data.append({
            'id': student.user_id,
            'name': f"{student.first_name} {student.last_name or ''}".strip(),
            'email': student.email,
            'last_message': last_message.content if last_message else 'No messages yet',
            'last_message_time': last_message.sent_at.isoformat() if last_message else None,
            'unread_count': unread_count
        })
    
    return render_template('chat/counselor_students.html', students=student_data)

@chat.route('/api/mark_messages_read', methods=['POST'])
@login_required
def mark_messages_read():
    """Mark messages as read"""
    try:
        data = request.get_json()
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return jsonify({'success': False, 'error': 'Sender ID required'}), 400
        
        # Mark all unread messages from sender as read
        unread_messages = Message.query.filter_by(
            sender_id=sender_id,
            receiver_id=current_user.user_id,
            read_at=None
        ).all()
        
        for msg in unread_messages:
            msg.mark_as_read()
        
        return jsonify({'success': True, 'marked_count': len(unread_messages)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500