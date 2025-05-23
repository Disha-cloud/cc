from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.message import Message
from models.activity import ActivityLog

# Add these functions to your existing auth.py file

@auth.route('/chat')
@login_required
def chat_list():
    """Show list of conversations for the user"""
    # Find all conversations for the current user
    sent_messages = Message.query.filter_by(sender_id=current_user.user_id).all()
    received_messages = Message.query.filter_by(receiver_id=current_user.user_id).all()
    
    # Get unique user ids from these messages
    user_ids = set()
    for msg in sent_messages:
        user_ids.add(msg.receiver_id)
    for msg in received_messages:
        user_ids.add(msg.sender_id)
        
    conversations = []
    for user_id in user_ids:
        other_user = User.query.get(user_id)
        if not other_user:
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
    
    return render_template('auth/chat_list.html', conversations=conversations)

@auth.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    """Show chat with specific user"""
    # Get the other user
    other_user = User.query.get_or_404(user_id)
    
    if current_user.user_role == 'student' and other_user.user_role != 'counsellor':
        flash('You can only chat with counselors.', 'danger')
        return redirect(url_for('auth.chat_list'))
    
    # Get conversation history
    messages = Message.query.filter(
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.user_id))
    ).order_by(Message.sent_at).all()
    
    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.user_id,
        read_at=None
    ).all()
    
    for msg in unread_messages:
        msg.read_at = datetime.utcnow()
    
    db.session.commit()
    
    # Determine which template to use based on user role
    if current_user.user_role == 'student':
        return render_template('auth/chat.html', counselor=other_user, messages=messages)
    else:
        return render_template('counsellor/chat.html', student=other_user, messages=messages)

@auth.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    
    if not receiver_id or not content:
        flash('Invalid message data.', 'danger')
        return redirect(url_for('auth.chat_list'))
    
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
        details=f'Sent message to user {receiver_id}'
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

@auth.route('/get_new_messages/<int:user_id>/<int:last_id>')
@login_required
def get_new_messages(user_id, last_id):
    """Get new messages since last_id"""
    new_messages = Message.query.filter(
        Message.id > last_id,
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.user_id))
    ).order_by(Message.sent_at).all()
    
    # Mark received messages as read
    for msg in new_messages:
        if msg.receiver_id == current_user.user_id and not msg.read_at:
            msg.read_at = datetime.utcnow()
    
    db.session.commit()
    
    # Format messages for JSON response
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'is_self': msg.sender_id == current_user.user_id,
            'time': msg.sent_at.strftime('%I:%M %p')
        })
    
    return jsonify(messages_data)