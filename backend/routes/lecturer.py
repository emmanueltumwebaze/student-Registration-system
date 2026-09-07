"""Lecturer routes"""
from flask import Blueprint
from routes.auth import lecturer_required
from flask_jwt_extended import get_jwt_identity
from app import db
from models import Lecturer, CourseLecturer, Course, Student, StudentCourse, AttendanceSession
from utils import ResponseHelper

lecturer_bp = Blueprint('lecturer', __name__)

# ==================== Lecturer Courses ====================

@lecturer_bp.route('/courses', methods=['GET'])
@lecturer_required
def get_assigned_courses():
    """Get courses assigned to lecturer"""
    lecturer_id = get_jwt_identity()
    
    # Get lecturer record
    lecturer = Lecturer.query.filter_by(user_id=lecturer_id).first()
    if not lecturer:
        return ResponseHelper.error('Lecturer record not found', 'NOT_FOUND', 404)
    
    try:
        # Get all course assignments for this lecturer
        assignments = CourseLecturer.query.filter_by(
            lecturer_id=lecturer.id,
            is_active=True
        ).all()
        
        result = []
        for assignment in assignments:
            course = Course.query.get(assignment.course_id)
            if course:
                # Get enrollment count
                enrollment_count = StudentCourse.query.filter_by(
                    course_id=course.id,
                    is_active=True
                ).count()
                
                # Get session count
                session_count = AttendanceSession.query.filter_by(
                    course_id=course.id
                ).count()
                
                result.append({
                    'assignment_id': assignment.id,
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'enrolled_students': enrollment_count,
                    'total_sessions': session_count,
                    'assigned_at': assignment.assigned_date.isoformat()
                })
        
        return ResponseHelper.success('Assigned courses retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve courses: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Lecturer Sessions ====================

@lecturer_bp.route('/sessions', methods=['GET'])
@lecturer_required
def get_my_sessions():
    """Get all sessions created by this lecturer"""
    lecturer_id = get_jwt_identity()
    
    # Get lecturer record
    lecturer = Lecturer.query.filter_by(user_id=lecturer_id).first()
    if not lecturer:
        return ResponseHelper.error('Lecturer record not found', 'NOT_FOUND', 404)
    
    try:
        sessions = AttendanceSession.query.filter_by(lecturer_id=lecturer.id).all()
        
        result = []
        for session in sessions:
            course = Course.query.get(session.course_id)
            if course:
                result.append({
                    'id': session.id,
                    'course_id': course.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'session_code': session.session_code,
                    'qr_code_data': session.qr_code_data,
                    'session_date': session.session_date.isoformat(),
                    'start_time': session.start_time.isoformat() if session.start_time else None,
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'duration_minutes': session.duration_minutes,
                    'status': session.status,
                    'created_at': session.created_at.isoformat()
                })
        
        # Sort by date descending
        result.sort(key=lambda x: x['session_date'], reverse=True)
        
        return ResponseHelper.success('Sessions retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve sessions: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Course Statistics ====================

@lecturer_bp.route('/courses/<int:course_id>/statistics', methods=['GET'])
@lecturer_required
def get_course_stats(course_id):
    """Get statistics for a specific course"""
    lecturer_id = get_jwt_identity()
    
    # Get lecturer record
    lecturer = Lecturer.query.filter_by(user_id=lecturer_id).first()
    if not lecturer:
        return ResponseHelper.error('Lecturer record not found', 'NOT_FOUND', 404)
    
    # Verify course is assigned to this lecturer
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    assignment = CourseLecturer.query.filter_by(
        course_id=course_id,
        lecturer_id=lecturer.id,
        is_active=True
    ).first()
    
    if not assignment:
        return ResponseHelper.error('Course not assigned to you', 'FORBIDDEN', 403)
    
    try:
        # Get enrollment count
        enrollment_count = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).count()
        
        # Get session count
        session_count = AttendanceSession.query.filter_by(course_id=course_id).count()
        
        # Get attendance data
        sessions = AttendanceSession.query.filter_by(course_id=course_id).all()
        session_ids = [s.id for s in sessions]
        
        if session_ids:
            from models import Attendance
            records = Attendance.query.filter(
                Attendance.session_id.in_(session_ids)
            ).all()
            total_attendance = len(records)
        else:
            total_attendance = 0
        
        avg_attendance = (total_attendance / (session_count * enrollment_count * 1.0)) * 100 if (session_count * enrollment_count) > 0 else 0
        
        stats = {
            'course_id': course_id,
            'course_code': course.code,
            'course_name': course.name,
            'enrolled_students': enrollment_count,
            'total_sessions': session_count,
            'total_attendance_records': total_attendance,
            'average_attendance': round(avg_attendance, 2)
        }
        
        return ResponseHelper.success('Course statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

