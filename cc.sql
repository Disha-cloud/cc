DROP DATABASE cc;
CREATE DATABASE cc;
USE cc;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    dob DATE,
    address TEXT,
    education_level VARCHAR(100),
    interests TEXT,
    counselor_id INT,
    password_hash VARCHAR(255) NOT NULL,
    user_role ENUM('student', 'counsellor', 'admin') DEFAULT 'student',
    course VARCHAR(100),
    date_registered DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL
);



CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    counsellor_id INT,
    appointment_date DATE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time TIME NULL,
    status ENUM('scheduled', 'completed', 'cancelled', 'rescheduled') DEFAULT 'scheduled',
    mode ENUM('online', 'offline', 'phone') NOT NULL,
    meeting_link VARCHAR(255),
    location VARCHAR(255),
    is_free BOOLEAN DEFAULT FALSE,
    fee DECIMAL(10,2),
    payment_status ENUM('paid', 'pending', 'not_required') DEFAULT 'not_required',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (counsellor_id) REFERENCES users(user_id)
);
CREATE TABLE counselling_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    notes TEXT,
    recommendations TEXT,
    resources TEXT,
    follow_up_date DATE,
    session_duration INT,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    student_id INT,
    counsellor_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES counselling_sessions(session_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (counsellor_id) REFERENCES users(user_id)
);
CREATE TABLE counsellor_schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    counsellor_id INT,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
    start_time TIME,
    end_time TIME,
    is_recurring BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (counsellor_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE career_resources (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    resource_type ENUM('document', 'video', 'link', 'other') NOT NULL,
    url VARCHAR(255),
    file_path VARCHAR(255),
    added_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (added_by) REFERENCES users(user_id)
);

CREATE TABLE student_documents (
    document_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    document_type ENUM('transcript', 'resume', 'certificate', 'other') NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    institution VARCHAR(100),
    field_of_study VARCHAR(100),
    graduation_year YEAR,
    career_interest TEXT,
    personality_test_results TEXT,
    skills TEXT,
    resume_link VARCHAR(255),
    FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN DEFAULT FALSE,
    notification_type ENUM('general', 'appointment', 'resource', 'payment') NOT NULL,
    related_entity_id INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT,
    recipient_id INT,
    message_text TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
);

CREATE TABLE administrators (
    admin_id INT PRIMARY KEY,
    department VARCHAR(100),
    role_description TEXT,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE student_resource_access (
    access_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    resource_id INT,
    access_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES career_resources(resource_id) ON DELETE CASCADE
);
CREATE TABLE CareerCounselors (
    counsellor_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    specialization VARCHAR(100),
    qualification TEXT,
    years_of_experience INT,
    bio TEXT,
    hourly_rate DECIMAL(10, 2),
    availability_status BOOLEAN,
    rating DECIMAL(3, 2),
    FOREIGN KEY (counsellor_id) REFERENCES users(user_id) ON DELETE CASCADE
);
SELECT * FROM users;