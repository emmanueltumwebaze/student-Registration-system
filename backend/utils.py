"""
Utility functions for the attendance system
"""
from app import db
from models import (Student, Lecturer, Attendance, AttendanceSession, 
                   AttendanceWarning, StudentCourse, Course, User)
from datetime import datetime, timedelta
from flask import jsonify
import qrcode
from io import BytesIO
import base64
import string
import random

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

class ReportGenerator:
    """Helper class for generating reports"""
    
    @staticmethod
    def generate_attendance_report(course_id, start_date=None, end_date=None):
        """Generate attendance report for a course"""
        if start_date is None:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow().date()
        
        # Get all sessions in date range
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
        
        return report
    
    @staticmethod
    def generate_student_report(student_id):
        """Generate comprehensive attendance report for a student"""
        student = Student.query.get(student_id)
        if not student:
            return None
        
        report = {
            'student_id': student.student_id,
            'student_name': f"{student.user.first_name} {student.user.last_name}",
            'courses': [],
            'overall_attendance': 0
        }
        
        # Get all enrolled courses
        enrollments = StudentCourse.query.filter_by(student_id=student_id, is_active=True).all()
        
        total_percentage = 0
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student_id, course.id
                )
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
    'ReportGenerator'
]
