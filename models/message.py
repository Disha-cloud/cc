from datetime import datetime
from models import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    message_type = db.Column(db.String(20), default='text')  # text, file, image
    file_path = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def mark_as_read(self):
        if not self.read_at:
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'message_type': self.message_type,
            'file_path': self.file_path,
            'sender_name': f"{self.sender.first_name} {self.sender.last_name or ''}".strip()
        }

class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id])
    counselor = db.relationship('User', foreign_keys=[counselor_id])
    
    @staticmethod
    def get_or_create(student_id, counselor_id):
        chat_room = ChatRoom.query.filter_by(
            student_id=student_id, 
            counselor_id=counselor_id
        ).first()
        
        if not chat_room:
            chat_room = ChatRoom(
                student_id=student_id,
                counselor_id=counselor_id
            )
            db.session.add(chat_room)
            db.session.commit()
        
        return chat_room
    
    def update_activity(self):
        self.last_activity = datetime.utcnow()
        db.session.commit()