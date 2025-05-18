from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.appointment import Appointment
from models.feedback import Feedback
from models.activity import ActivityLog
from forms.user import UserForm
from utils.decorators import role_required

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    # Count users by role
    user_count = User.query.filter_by(role='user').count()
    counselor_count = User.query.filter_by(role='counselor').count()
    admin_count = User.query.filter_by(role='admin').count()
    
    # Count appointments by status
    pending_count = Appointment.query.filter_by(status='pending').count()
    confirmed_count = Appointment.query.filter_by(status='confirmed').count()
    completed_count = Appointment.query.filter_by(status='completed').count()
    cancelled_count = Appointment.query.filter_by(status='cancelled').count()
    
    # Recent activity
    recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        counselor_count=counselor_count,
        admin_count=admin_count,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        recent_activity=recent_activity
    )

@admin.route('/users')
@login_required
@role_required('admin')
def users():
    role_filter = request.args.get('role', 'all')
    
    if role_filter != 'all':
        users = User.query.filter_by(role=role_filter).all()
    else:
        users = User.query.all()
    
    return render_template('admin/users.html', users=users, current_filter=role_filter)

@admin.route('/user/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_user():
    form = UserForm()
    
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        
        if existing_user:
            flash('Email already registered.', 'danger')
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                student_id=form.student_id.data if form.role.data == 'user' else None,
                phone=form.phone.data,
                course=form.course.data if form.role.data == 'user' else None,
                role=form.role.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            
            # Log activity
            log = ActivityLog(
                user_id=current_user.id,
                action='Create User',
                details=f'Created new {form.role.data}: {form.name.data}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'New {form.role.data} created successfully!', 'success')
            return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='New User')

@admin.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.role = form.role.data
        
        if form.role.data == 'user':
            user.student_id = form.student_id.data
            user.course = form.course.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action='Update User',
            details=f'Updated {user.role}: {user.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='Edit User')

@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='Delete User',
        details=f'Deleted {user.role}: {user.name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/activity')
@login_required
@role_required('admin')
def activity():
    page = request.args.get('page', 1, type=int)
    activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc())\
        .paginate(page=page, per_page=20)
    
    return render_template('admin/activity.html', activities=activities)

@admin.route('/api/activity/latest')
@login_required
@role_required('admin')
def latest_activity():
    last_id = request.args.get('last_id', 0, type=int)
    
    new_activities = ActivityLog.query.filter(ActivityLog.id > last_id)\
        .order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    activities = []
    for activity in new_activities:
        activities.append({
            'id': activity.id,
            'user': activity.user.name,
            'action': activity.action,
            'details': activity.details,
            'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(activities)