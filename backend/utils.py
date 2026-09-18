"""
Utility functions for the attendance system
"""
from app import db
from models import (Student, Lecturer, Attendance, AttendanceSession, AttendanceWarning, StudentCourse, Course, User)
from datetime import datetime, timedelta
from flask import jsonify
import qrcode
from io import BytesIO
import base64
import string
import random
import secrets
from email.message import EmailMessage
import os
import requests
from flask import current_app

class AttendanceCalculator:
    """Helper class for attendance calculations"""
    @staticmethod
    def calculate_attendance_percentage(student_id, course_id):
        """Calculate attendance percentage for student in course"""
        # Get all attendance sessions for the course
        sessions = AttendanceSession.query.filter_by(course_id=course_id).all()
        if not sessions:
            return 0
        total_sessions = len(sessions)
        present_count = 0
        for session in sessions:
            attendance = Attendance.query.filter_by(
                session_id=session.id,
                student_id=student_id,
                status='present'
            ).first()
            if attendance:
                present_count += 1
        percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
        return round(percentage, 2)
    @staticmethod
    def get_student_attendance_summary(student_id):
        """Get attendance summary for a student across all courses"""
        courses = StudentCourse.query.filter_by(student_id=student_id, is_active=True).all()
        summary = []
        for enrollment in courses:
            course = Course.query.get(enrollment.course_id)
            if course:
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student_id, course.id
                )
                summary.append({
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'attendance_percentage': percentage
                })
        return summary
    @staticmethod
    def get_course_attendance_summary(course_id):
        """Get attendance summary for all students in a course"""
        enrollments = StudentCourse.query.filter_by(course_id=course_id, is_active=True).all()
        summary = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if student and student.user:
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student.id, course_id
                )
                summary.append({
                    'student_id': student.id,
                    'student_number': student.student_id,
                    'student_name': f"{student.user.first_name} {student.user.last_name}",
                    'attendance_percentage': percentage
                })
        return sorted(summary, key=lambda x: x['attendance_percentage'])
    @staticmethod
    def identify_low_attendance_students(course_id, threshold=75):
        """Identify students with attendance below threshold"""
        summary = AttendanceCalculator.get_course_attendance_summary(course_id)
        low_attendance = [s for s in summary if s['attendance_percentage'] < threshold]
        return low_attendance

    @staticmethod
    def create_attendance_warnings(threshold=75, critical_threshold=50):
        """Create attendance warnings for all students"""
        # Get all active courses
        courses = Course.query.filter_by(is_active=True).all()
        warnings_created = 0

        for course in courses:
            students = AttendanceCalculator.get_course_attendance_summary(course.id)
            for student_data in students:
                student_id = student_data['student_id']
                percentage = student_data['attendance_percentage']
                # Delete old warning for this student-course
                AttendanceWarning.query.filter_by(
                    student_id=student_id,
                    course_id=course.id
                ).delete()
                # Create new warning if needed
                if percentage < critical_threshold:
                    warning = AttendanceWarning(
                        student_id=student_id,
                        course_id=course.id,
                        attendance_percentage=percentage,
                        warning_level='critical'
                    )
                    db.session.add(warning)
                    warnings_created += 1
                elif percentage < threshold:
                    warning = AttendanceWarning(
                        student_id=student_id,
                        course_id=course.id,
                        attendance_percentage=percentage,
                        warning_level='low'
                    )
                    db.session.add(warning)
                    warnings_created += 1
        
        db.session.commit()
        return warnings_created

class QRCodeGenerator:
    """Helper class for QR code generation"""
    
    @staticmethod
    def generate_qr_code(data, size=10, border=4):
        """Generate QR code and return as base64 data URL"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

class SessionCodeGenerator:
    """Helper class for generating unique session codes"""
    
    @staticmethod
    def generate_unique_code(prefix='SES', length=6):
        """Generate a unique session code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = prefix + ''.join(random.choices(chars, k=length))
            # Check if code already exists
            if not AttendanceSession.query.filter_by(session_code=code).first():
                return code

class ResponseHelper:
    """Helper class for standardized API responses"""
    
    @staticmethod
    def success(message='Success', data=None, status_code=200):
        """Return success response"""
        response = {'message': message}
        if data is not None:
            response['data'] = data
        return jsonify(response), status_code
    
    @staticmethod
    def error(message='Error', error_code=None, status_code=400):
        """Return error response"""
        response = {'error': message}
        if error_code:
            response['error_code'] = error_code
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(items, page=1, per_page=10):
        """Return paginated response"""
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = items[start:end]
        
        return {
            'items': paginated_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }

class DateTimeHelper:
    """Helper class for date/time operations"""
    
    @staticmethod
    def get_today():
        """Get today's date"""
        return datetime.utcnow().date()
    
    @staticmethod
    def get_now():
        """Get current datetime"""
        return datetime.utcnow()
    
    @staticmethod
    def days_ago(days):
        """Get date from N days ago"""
        return datetime.utcnow() - timedelta(days=days)
    
    @staticmethod
    def format_datetime(dt):
        """Format datetime to ISO string"""
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)

class ValidationHelper:
    """Helper class for input validation"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_required_fields(data, fields):
        """Validate that required fields are present"""
        missing = []
        for field in fields:
            if field not in data or not data[field]:
                missing.append(field)
        return missing
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        return True, "Password is valid"

class EmailHelper:
    """Helper class for sending temporary passwords via email."""

    @staticmethod
    def generate_temporary_password(length=12):
        """Generate a temporary password that includes letters and digits."""
        alphabet = string.ascii_letters + string.digits
        while True:
            pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
            if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd) and any(c.isdigit() for c in pwd):
                return pwd

    @staticmethod
    def send_temporary_password_email(to_email, first_name, last_name, temporary_password, role="student"):
        """Send a temporary password, falling back to console logging when SMTP is unset."""
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")

        if not api_key or not sender_email:
            print(f"BREVO keys missing. Console fallback for {to_email}.")
            return {
                "success": True,
                "method": "console",
                "message": f"Temporary password for {first_name} {last_name}: {temporary_password}"
            }

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {"api-key": api_key, "Content-Type": "application/json"}

        html = f"""
        <h2>Hello {first_name} {last_name},</h2>
        <p>Your {role} account has been created.</p>
        <p><b>Email:</b> {to_email}</p>
        <p><b>Temporary Password:</b> <span style="background:#eee;padding:8px;font-size:18px;">{temporary_password}</span></p>
        <p>Login: https://student-attendance-portal-gx6o.onrender.com</p>
        <p>Please change password after login.</p>
        """

        payload = {
            "sender": {"email": sender_email, "name": "Student Portal"},
            "to": [{"email": to_email}],
            "subject": "Your Temporary Password",
            "htmlContent": html
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            print(f"Brevo: {response.status_code} {response.text}")
            if response.status_code in [200, 201]:
                return {"success": True, "method": "smtp", "status": "sent"}
            return {"success": False, "method": "failed", "error": response.text}
        except Exception as exc:
            print(f"Brevo error: {exc}")
            return {"success": False, "method": "failed", "error": str(exc)}


class ReportGenerator:
    """Helper class for generating attendance reports."""

    @staticmethod
    def get_session_in_date_range(course_id, start_date, end_date):
        """Get all sessions for a course within a date range."""
        sessions = AttendanceSession.query.filter(
            AttendanceSession.course_id == course_id,
            AttendanceSession.session_date >= start_date,
            AttendanceSession.session_date <= end_date
        ).all()

        report = {
            'course_id': course_id,
            'course': Course.query.get(course_id).to_dict() if course_id else None,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_sessions': len(sessions),
            'sessions': [],
            'summary': {}
        }

        for session in sessions:
            attendance_records = Attendance.query.filter_by(session_id=session.id).all()
            session_data = session.to_dict()
            session_data['attendance_count'] = len(attendance_records)
            session_data['present_count'] = len([a for a in attendance_records if a.status == 'present'])
            report['sessions'].append(session_data)

        if sessions:
            report['summary'] = {
                'total_attendance_records': sum(len(Attendance.query.filter_by(session_id=session.id).all()) for session in sessions),
                'present_records': sum(
                    len([a for a in Attendance.query.filter_by(session_id=session.id).all() if a.status == 'present'])
                    for session in sessions
                )
            }

        return report

    @staticmethod
    def generate_attendance_report(course_id, start_date=None, end_date=None):
        """Generate a detailed attendance report for a course."""
        course = Course.query.get(course_id)
        if not course:
            return None

        query = AttendanceSession.query.filter_by(course_id=course_id)
        if start_date is not None:
            query = query.filter(AttendanceSession.session_date >= start_date)
        if end_date is not None:
            query = query.filter(AttendanceSession.session_date <= end_date)

        sessions = query.order_by(AttendanceSession.session_date.asc()).all()
        student_ids = [row.student_id for row in StudentCourse.query.filter_by(course_id=course_id, is_active=True).all()]

        report = {
            'course_id': course.id,
            'course_name': course.name,
            'course_code': course.code,
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
            },
            'total_sessions': len(sessions),
            'sessions': [],
            'students': []
        }

        for session in sessions:
            attendance_records = Attendance.query.filter_by(session_id=session.id).all()
            session_data = session.to_dict()
            session_data['attendance_count'] = len(attendance_records)
            session_data['present_count'] = len([record for record in attendance_records if record.status == 'present'])
            report['sessions'].append(session_data)

        for student_id in sorted(set(student_ids)):
            student = Student.query.get(student_id)
            if not student or not student.user:
                continue
            percentage = AttendanceCalculator.calculate_attendance_percentage(student_id, course_id)
            report['students'].append({
                'student_id': student.id,
                'student_number': student.student_id,
                'student_name': f"{student.user.first_name} {student.user.last_name}",
                'attendance_percentage': percentage,
            })

        report['students'] = sorted(report['students'], key=lambda s: s['attendance_percentage'])
        return report

    @staticmethod
    def generate_student_report(student_id):
        """Generate a full attendance report for a single student."""
        student = Student.query.get(student_id)
        if not student:
            return None

        report = {
            'student_id': student.student_id,
            'student_name': f"{student.user.first_name} {student.user.last_name}",
            'courses': [],
            'overall_attendance': 0
        }

        enrollments = StudentCourse.query.filter_by(student_id=student_id, is_active=True).all()
        total_percentage = 0
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                percentage = AttendanceCalculator.calculate_attendance_percentage(student_id, course.id)
                report['courses'].append({
                    'course_code': course.code,
                    'course_name': course.name,
                    'attendance_percentage': percentage
                })
                total_percentage += percentage

        if report['courses']:
            report['overall_attendance'] = round(total_percentage / len(report['courses']), 2)

        return report


# Export all helper classes
__all__ = [
    'AttendanceCalculator',
    'QRCodeGenerator',
    'SessionCodeGenerator',
    'ResponseHelper',
    'DateTimeHelper',
    'ValidationHelper',
    'EmailHelper',
    'ReportGenerator'
]
