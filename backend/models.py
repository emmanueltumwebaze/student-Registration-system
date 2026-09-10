"""
Database Models for Student Attendance System
"""
from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import hashlib

class UserRole(Enum):
    """User roles"""
    ADMIN = 'admin'
    LECTURER = 'lecturer'
    STUDENT = 'student'

class AttendanceStatus(Enum):
    """Attendance status"""
    PRESENT = 'present'
    ABSENT = 'absent'
    LATE = 'late'

class User(db.Model):
    """User model for all system users"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True, index=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    lecturer = db.relationship('Lecturer', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'must_change_password': self.must_change_password,
            'created_at': self.created_at.isoformat()
        }

class ActivationToken(db.Model):
    """One-time token used by a new user to choose their password."""
    __tablename__ = 'activation_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activation_token', uselist=False,
                                                       cascade='all, delete-orphan'))

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def is_valid(self):
        return self.used_at is None and self.expires_at > datetime.utcnow()

class Department(db.Model):
    """Department model"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    programs = db.relationship('Program', backref='department', cascade='all, delete-orphan')
    lecturers = db.relationship('Lecturer', backref='department', cascade='all, delete-orphan')
    students = db.relationship('Student', backref='department', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

class Program(db.Model):
    """Program/Degree model"""
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    duration_years = db.Column(db.Integer, default=4)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='program', cascade='all, delete-orphan')
    students = db.relationship('Student', backref='program', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('name', 'department_id', name='_program_dept_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'department_id': self.department_id,
            'duration_years': self.duration_years,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

class Course(db.Model):
    """Course model"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course_lecturers = db.relationship('CourseLecturer', backref='course', cascade='all, delete-orphan')
    student_courses = db.relationship('StudentCourse', backref='course', cascade='all, delete-orphan')
    attendance_sessions = db.relationship('AttendanceSession', backref='course', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'credits': self.credits,
            'program_id': self.program_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_courses = db.relationship('StudentCourse', backref='student', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='student', cascade='all, delete-orphan')
    warnings = db.relationship('AttendanceWarning', backref='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_id': self.student_id,
            'program_id': self.program_id,
            'department_id': self.department_id,
            'enrollment_date': self.enrollment_date.isoformat(),
            'is_active': self.is_active,
            'user': self.user.to_dict() if self.user else None
        }

class Lecturer(db.Model):
    """Lecturer model"""
    __tablename__ = 'lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lecturer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    specialization = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course_lecturers = db.relationship('CourseLecturer', backref='lecturer', cascade='all, delete-orphan')
    attendance_sessions = db.relationship('AttendanceSession', backref='lecturer', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lecturer_id': self.lecturer_id,
            'department_id': self.department_id,
            'specialization': self.specialization,
            'is_active': self.is_active,
            'user': self.user.to_dict() if self.user else None
        }

class CourseLecturer(db.Model):
    """Course-Lecturer assignment"""
    __tablename__ = 'course_lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    __table_args__ = (db.UniqueConstraint('course_id', 'lecturer_id', name='_course_lecturer_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'lecturer_id': self.lecturer_id,
            'assigned_date': self.assigned_date.isoformat(),
            'is_active': self.is_active
        }

class StudentCourse(db.Model):
    """Student course registration"""
    __tablename__ = 'student_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'is_active': self.is_active
        }

class AttendanceSession(db.Model):
    """Attendance session for tracking"""
    __tablename__ = 'attendance_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    session_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    qr_code_data = db.Column(db.Text, nullable=False)  # Contains QR code data URL
    session_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='active', index=True)  # active, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='session', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'lecturer_id': self.lecturer_id,
            'session_code': self.session_code,
            'session_date': self.session_date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class Attendance(db.Model):
    """Attendance record"""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='present', index=True)  # present, absent, late
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('session_id', 'student_id', name='_session_student_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'student_id': self.student_id,
            'check_in_time': self.check_in_time.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class AttendanceWarning(db.Model):
    """Low attendance warning for students"""
    __tablename__ = 'attendance_warnings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    attendance_percentage = db.Column(db.Float, nullable=False)
    warning_level = db.Column(db.String(20), default='low')  # low, critical
    is_acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'attendance_percentage': self.attendance_percentage,
            'warning_level': self.warning_level,
            'is_acknowledged': self.is_acknowledged,
            'created_at': self.created_at.isoformat()
        }
