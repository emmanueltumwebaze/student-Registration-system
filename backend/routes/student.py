"""Student routes"""
from flask import Blueprint, request
from routes.auth import student_required
from flask_jwt_extended import get_jwt_identity
from app import db
from models import Student, StudentCourse, Course, Attendance, AttendanceSession, AttendanceWarning, Lecturer
from utils import ResponseHelper, AttendanceCalculator

student_bp = Blueprint('student', __name__)

# ==================== Student Courses ====================

@student_bp.route('/courses', methods=['GET'])
@student_required
def get_student_courses():
    """Get student's registered courses"""
    student_id = get_jwt_identity()
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    try:
        # Get all active course enrollments
        enrollments = StudentCourse.query.filter_by(
            student_id=student.id,
            is_active=True
        ).all()
        
        result = []
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                # Get lecturer info
                lecturer_name = 'TBA'
                from models import CourseLecturer
                cl = CourseLecturer.query.filter_by(course_id=course.id, is_active=True).first()
                if cl:
                    lecturer = Lecturer.query.get(cl.lecturer_id)
                    if lecturer:
                        lecturer_name = f"{lecturer.user.first_name} {lecturer.user.last_name}"
                
                # Get attendance percentage
                attendance_percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student.id, course.id
                )
                
                result.append({
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'lecturer_name': lecturer_name,
                    'attendance_percentage': attendance_percentage,
                    'enrolled_at': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
                    'is_active': enrollment.is_active
                })
        
        return ResponseHelper.success('Student courses retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve courses: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Attendance History ====================

@student_bp.route('/attendance', methods=['GET'])
@student_required
def get_attendance_history():
    """Get student's attendance records"""
    student_id = get_jwt_identity()
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    try:
        # Get all attendance records for student
        records = Attendance.query.filter_by(student_id=student.id).all()
        
        result = []
        for record in records:
            session = AttendanceSession.query.get(record.session_id)
            course = Course.query.get(session.course_id) if session else None
            
            if session and course:
                result.append({
                    'id': record.id,
                    'session_id': session.id,
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'session_date': session.session_date.isoformat(),
                    'check_in_time': record.check_in_time.isoformat(),
                    'status': record.status
                })
        
        # Sort by date descending
        result.sort(key=lambda x: x['check_in_time'], reverse=True)
        
        return ResponseHelper.success('Attendance history retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve attendance: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Attendance Warnings ====================

@student_bp.route('/warnings', methods=['GET'])
@student_required
def get_warnings():
    """Get student's attendance warnings"""
    student_id = get_jwt_identity()
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    try:
        warnings = AttendanceWarning.query.filter_by(student_id=student.id).all()
        
        result = []
        for warning in warnings:
            course = Course.query.get(warning.course_id)
            if course:
                result.append({
                    'id': warning.id,
                    'student_id': student.id,
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'attendance_percentage': warning.attendance_percentage,
                    'warning_level': warning.warning_level,
                    'created_at': warning.created_at.isoformat(),
                    'is_acknowledged': warning.is_acknowledged
                })
        
        # Sort by warning level (critical first) and date
        result.sort(key=lambda x: (x['warning_level'] != 'critical', x['created_at']), reverse=True)
        
        return ResponseHelper.success('Warnings retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve warnings: {str(e)}', 'QUERY_ERROR', 500)

@student_bp.route('/warnings/<int:warning_id>/acknowledge', methods=['PUT'])
@student_required
def acknowledge_warning(warning_id):
    """Acknowledge an attendance warning"""
    student_id = get_jwt_identity()
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    # Get warning
    warning = AttendanceWarning.query.get(warning_id)
    if not warning:
        return ResponseHelper.error('Warning not found', 'NOT_FOUND', 404)
    
    # Verify warning belongs to student
    if warning.student_id != student.id:
        return ResponseHelper.error('Access denied', 'FORBIDDEN', 403)
    
    try:
        warning.is_acknowledged = True
        db.session.commit()
        return ResponseHelper.success('Warning acknowledged', warning.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

# ==================== Statistics ====================

@student_bp.route('/statistics', methods=['GET'])
@student_required
def get_statistics():
    """Get student's attendance statistics"""
    student_id = get_jwt_identity()
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    try:
        summary = AttendanceCalculator.get_student_attendance_summary(student.id)
        
        stats = {
            'student_id': student.id,
            'student_number': student.student_id,
            'student_name': f"{student.user.first_name} {student.user.last_name}",
            'courses': summary,
            'overall_average': sum(c['attendance_percentage'] for c in summary) / len(summary) if summary else 0,
            'low_courses': sum(1 for c in summary if c['attendance_percentage'] < 75),
            'critical_courses': sum(1 for c in summary if c['attendance_percentage'] < 50)
        }
        
        return ResponseHelper.success('Statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

