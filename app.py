import os
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Feedback  # Ensure Feedback is imported
from routes import init_app
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Register routes/blueprints
    init_app(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/auth/login', methods=['GET', 'POST'])
    def auth_login():
        if current_user.is_authenticated:
            return redirect(url_for('student_dashboard'))

        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()

                if user.user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.user_role == 'counsellor':
                    return redirect(url_for('counsellor_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html')

    @app.route('/auth/register', methods=['GET', 'POST'])
    def auth_register():
        if current_user.is_authenticated:
            return redirect(url_for('student_dashboard'))

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            dob = request.form.get('dob')
            address = request.form.get('address')
            education_level = request.form.get('education_level')
            interests = request.form.getlist('interests')
            counselor_id = request.form.get('selected_counselor_id')
            interests_str = ','.join(interests)

            hashed_password = generate_password_hash(password)
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                dob=dob,
                address=address,
                education_level=education_level,
                interests=interests_str,
                counselor_id=counselor_id,
                password_hash=hashed_password,
                user_role='student',
                date_registered=datetime.utcnow()
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth_login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Registration failed: {e}', 'danger')

        return render_template('auth/register.html')

    @app.route('/registration_success')
    def registration_success():
        return render_template('auth/regs.html')

    @app.route('/auth/dashboard')
    @login_required
    def student_dashboard():
        if current_user.user_role == 'student':
            student = current_user
            counselor = User.query.get(student.counselor_id)
            student.counselor_name = f"{counselor.first_name} {counselor.last_name}" if counselor else "Not Assigned"
            return render_template('auth/dashboard.html', student=student)
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.user_role == 'admin':
            return render_template('admin/dashboard.html')
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

    @app.route('/counsellor/register', methods=['GET', 'POST'])
    def register_counsellor():
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            specialization = request.form.get('specialization')
            phone = request.form.get('phone')
            resume = request.files.get('resume')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(request.url)

            resume_filename = None
            if resume and resume.filename != '':
                filename = secure_filename(resume.filename)
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
                os.makedirs(resume_path, exist_ok=True)
                full_resume_path = os.path.join(resume_path, filename)
                resume.save(full_resume_path)
                resume_filename = filename

            hashed_password = generate_password_hash(password)
            new_counsellor = User(
                first_name=full_name,
                last_name='',
                email=email,
                password_hash=hashed_password,
                user_role='counsellor',
                phone=phone,
                specialization=specialization,
                resume=resume_filename,
                date_registered=datetime.utcnow()
            )

            db.session.add(new_counsellor)
            db.session.commit()
            flash('Counsellor registration successful! Please log in.', 'success')
            return redirect(url_for('counsellor_login'))

        return render_template('counsellor/register.html')

    @app.route('/counsellor/login', methods=['GET', 'POST'])
    def counsellor_login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email, user_role='counsellor').first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Login successful!', 'success')
                return redirect(url_for('counsellor_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        return render_template('counsellor/login.html')

    @app.route('/counsellor/dashboard')
    @login_required
    def counsellor_dashboard():
        if current_user.user_role == 'counsellor':
            return render_template('counsellor/dashboard.html')
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

    @app.route('/auth/appointment', methods=['GET', 'POST'])
    @login_required
    def appointment():
        if current_user.user_role != 'student':
            flash("Only students can book appointments.", "danger")
            return redirect(url_for('index'))

        student = current_user

        if request.method == 'POST':
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            purpose = request.form.get('purpose')

            # Here you could add saving to the database

            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('student_dashboard'))

        return render_template('auth/appointment.html', student=student)

    @app.route('/auth/feedback', methods=['GET'])
    @login_required
    def feedback_form():
        if current_user.user_role != 'student':
            flash("Only students can give feedback.", "danger")
            return redirect(url_for('index'))

        student = current_user
        assigned_mentor = User.query.filter_by(id=student.counselor_id).first()

        return render_template(
            'feedback.html',
            mentor_name=assigned_mentor.first_name + " " + assigned_mentor.last_name if assigned_mentor else "No Mentor Assigned",
            mentor_id=assigned_mentor.id if assigned_mentor else None
        )

    @app.route('/submit_feedback', methods=['POST'])
    @login_required
    def submit_feedback():
        try:
            feedback_type = request.form.get('feedback_type')
            feedback_text = request.form.get('feedback')
            mentor_id = request.form.get('mentor_id') if feedback_type == 'mentor' else None

            new_feedback = Feedback(
                student_id=current_user.id,
                feedback_type=feedback_type,
                feedback_text=feedback_text,
                mentor_id=mentor_id,
                date_submitted=datetime.utcnow()
            )
            db.session.add(new_feedback)
            db.session.commit()

            flash("Thank you for your feedback!", "success")
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            db.session.rollback()
            print("Error submitting feedback:", e)
            flash("An error occurred while submitting feedback.", "danger")
            return redirect(url_for('feedback_form'))

    events = [
        {"title": "Career Fair", "date": "2025-05-27", "description": "A virtual career expo with 30+ companies."},
        {"title": "STEM Workshop", "date": "2025-05-30", "description": "Hands-on learning for STEM careers."},
        {"title": "Resume Building Webinar", "date": "2025-06-20", "description": "Tips to create standout resumes."},
    ]

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/events")
    def events_page():
        today = datetime.today().date()
        upcoming = [e for e in events if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today]
        return render_template("events.html", events=upcoming)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('index'))

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'File uploaded successfully', 200

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.route('/ping')
    def ping():
        return "App is running!", 200

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
