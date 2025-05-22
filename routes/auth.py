from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db
from models.user import User
from forms.auth import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on user_role
        if current_user.user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.user_role == 'counsellor':
            return redirect(url_for('counsellor_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if user.user_role == 'admin':
                return redirect(next_page or url_for('admin_dashboard'))
            elif user.user_role == 'counsellor':
                return redirect(next_page or url_for('counsellor_dashboard'))
            else:
                return redirect(next_page or url_for('student_dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.user_role == 'counsellor':
            return redirect(url_for('counsellor_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
        else:
            user = User(
                first_name=form.name.data,
                email=form.email.data,
                course=form.course.data,
                user_role=form.role.data  # Make sure this field exists in your RegisterForm
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
