from app import app, db
from models.user import User
from models.activity import ActivityLog
from datetime import datetime

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            # Create admin user
            admin = User(
                name='Administrator',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Log activity
            log = ActivityLog(
                user_id=1,  # Will be admin's ID
                action='System Initialization',
                details='Created admin account'
            )
            db.session.add(log)
            
            # Create sample counselor
            counselor = User(
                name='John Counselor',
                email='counselor@example.com',
                phone='1234567890',
                role='counselor'
            )
            counselor.set_password('counselor123')
            db.session.add(counselor)
            
            # Log activity
            log = ActivityLog(
                user_id=1,
                action='System Initialization',
                details='Created sample counselor account'
            )
            db.session.add(log)
            
            # Create sample student
            student = User(
                name='Alice Student',
                email='student@example.com',
                student_id='ST12345',
                phone='9876543210',
                course='Computer Science',
                role='user'
            )
            student.set_password('student123')
            db.session.add(student)
            
            # Log activity
            log = ActivityLog(
                user_id=1,
                action='System Initialization',
                details='Created sample student account'
            )
            db.session.add(log)
            
            db.session.commit()
            
            print('Database initialized with sample users.')
        else:
            print('Database already has admin user, skipping initialization.')

if __name__ == '__main__':
    init_db()