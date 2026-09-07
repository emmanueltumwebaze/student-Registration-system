"""Routes package"""
from .auth import auth_bp
from .admin import admin_bp
from .assignments import assignments_bp
from .attendance import attendance_bp
from .reports import reports_bp
from .lecturer import lecturer_bp
from .student import student_bp

__all__ = ['auth_bp', 'admin_bp', 'assignments_bp', 'attendance_bp', 'reports_bp', 'lecturer_bp', 'student_bp']
