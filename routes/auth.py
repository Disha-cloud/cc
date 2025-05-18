from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db
from models.user import User
from models.activity import ActivityLog
from forms.auth import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            
            # Log activity
            log = ActivityLog(
                user_id=user.id,
                action='Login',
                details=f'User logged in from {request.remote_addr}'
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page or url_for('admin.dashboard'))
            elif user.role == 'counselor':
                return redirect(next_page or url_for('counselor.dashboard'))
            else:
                return redirect(next_page or url_for('user.dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        existing_student_id = User.query.filter_by(student_id=form.student_id.data).first()
        
        if existing_user:
            flash('Email already registered.', 'danger')
        elif existing_student_id:
            flash('Student ID already registered.', 'danger')
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                student_id=form.student_id.data,
                phone=form.phone.data,
                course=form.course.data,
                role='user'
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            
            # Log activity
            log = ActivityLog(
                user_id=user.id,
                action='Register',
                details=f'New user registered from {request.remote_addr}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='Logout',
        details=f'User logged out from {request.remote_addr}'
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))