import os
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User  # Ensure User model is properly imported
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
    login_manager.login_view = 'auth_login'  # Redirect to login if not authenticated

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Set upload folder path and create it if not exists
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Register blueprints/routes
    init_app(app)

    # Home route rendering index.html
    @app.route('/')
    def index():
        return render_template('index.html')

    # User Login and Register
    @app.route('/auth/login', methods=['GET', 'POST'])
    def auth_login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email, role='student').first()  # Only students

            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        
        return render_template('auth/login.html')

    @app.route('/auth/register', methods=['GET', 'POST'])
    def auth_register():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password, role='student')
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth_login'))
        
        return render_template('auth/register.html')

    # Counsellor Login and Register
    @app.route('/counsellor/login', methods=['GET', 'POST'])
    def counsellor_login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email, role='counsellor').first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('counsellor_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')

        return render_template('counsellor/login.html')

    @app.route('/counsellor/register', methods=['GET', 'POST'])
    def counsellor_register():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password, role='counsellor')
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('counsellor_login'))
        
        return render_template('counsellor/register.html')

    # Student Dashboard
    @app.route('/auth/dashboard')
    @login_required
    def student_dashboard():
        if current_user.role == 'student':
            return render_template('auth/dashboard.html')
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

    # Counsellor Dashboard
    @app.route('/counsellor/dashboard')
    @login_required
    def counsellor_dashboard():
        if current_user.role == 'counsellor':
            return render_template('counsellor/dashboard.html')
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

    # Logout Route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('index'))

    # File upload route
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

    # Error handler for 500
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
