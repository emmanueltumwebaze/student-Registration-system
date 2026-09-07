"""Attendance management routes"""
from flask import Blueprint, request, send_file
from routes.auth import admin_required, lecturer_required, student_required
from flask_jwt_extended import get_jwt_identity, get_jwt, jwt_required
from app import db
from models import (AttendanceSession, Attendance, Student, Course, Lecturer, 
                   User, StudentCourse, AttendanceWarning)
from utils import (ResponseHelper, ValidationHelper, QRCodeGenerator, 
                  SessionCodeGenerator, AttendanceCalculator, DateTimeHelper)
from datetime import datetime, time, timedelta
import io

attendance_bp = Blueprint('attendance', __name__)

# ==================== Attendance Session Management ====================

@attendance_bp.route('/sessions', methods=['GET'])
@admin_required
def list_sessions():
    """List all attendance sessions"""
    try:
        sessions = AttendanceSession.query.all()
        result = []
        for session in sessions:
            data = session.to_dict()
            course = Course.query.get(session.course_id)
            lecturer = Lecturer.query.get(session.lecturer_id)
            if course and lecturer:
                data['course_code'] = course.code
                data['course_name'] = course.name
                data['lecturer_name'] = f"{lecturer.user.first_name} {lecturer.user.last_name}"
            result.append(data)
        return ResponseHelper.success('Sessions retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/sessions', methods=['POST'])
@lecturer_required
def create_session():
    """Create new attendance session"""
    lecturer_id = get_jwt_identity()
    user = User.query.get(lecturer_id)
    
    # Get lecturer record
    lecturer = Lecturer.query.filter_by(user_id=lecturer_id).first()
    if not lecturer:
        return ResponseHelper.error('Lecturer record not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    required = ['course_id', 'session_date', 'start_time', 'end_time']
    missing = ValidationHelper.validate_required_fields(data, required)
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    # Verify course exists and lecturer is assigned
    course = Course.query.get(data['course_id'])
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        # Generate unique session code
        session_code = SessionCodeGenerator.generate_unique_code()
        
        # Parse times
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        session_date = datetime.strptime(data['session_date'], '%Y-%m-%d').date()
        
        # Calculate duration
        start_dt = datetime.combine(session_date, start_time)
        end_dt = datetime.combine(session_date, end_time)
        duration = int((end_dt - start_dt).total_seconds() / 60)
        
        if duration <= 0:
            return ResponseHelper.error('End time must be after start time', 'INVALID_DATA', 400)
        
        # Generate QR code with session code
        qr_data = QRCodeGenerator.generate_qr_code(session_code)
        
        # Create session
        session = AttendanceSession(
            course_id=data['course_id'],
            lecturer_id=lecturer.id,
            session_code=session_code,
            qr_code_data=qr_data,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            status='active'
        )
        
        db.session.add(session)
        db.session.commit()
        
        result = session.to_dict()
        result['course_code'] = course.code
        result['course_name'] = course.name
        
        return ResponseHelper.success('Session created', result, 201)
    except ValueError as e:
        return ResponseHelper.error(f'Invalid date/time format: {str(e)}', 'INVALID_DATA', 400)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Creation failed: {str(e)}', 'CREATE_ERROR', 500)

@attendance_bp.route('/sessions/<int:session_id>', methods=['GET'])
@admin_required
def get_session(session_id):
    """Get specific attendance session"""
    session = AttendanceSession.query.get(session_id)
    if not session:
        return ResponseHelper.error('Session not found', 'NOT_FOUND', 404)
    
    data = session.to_dict()
    course = Course.query.get(session.course_id)
    lecturer = Lecturer.query.get(session.lecturer_id)
    if course and lecturer:
        data['course_code'] = course.code
        data['course_name'] = course.name
        data['lecturer_name'] = f"{lecturer.user.first_name} {lecturer.user.last_name}"
    
    return ResponseHelper.success('Session retrieved', data, 200)

@attendance_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@lecturer_required
def update_session(session_id):
    """Update attendance session"""
    session = AttendanceSession.query.get(session_id)
    if not session:
        return ResponseHelper.error('Session not found', 'NOT_FOUND', 404)
    
    # Verify lecturer owns this session
    lecturer = Lecturer.query.filter_by(user_id=get_jwt_identity()).first()
    if not lecturer or session.lecturer_id != lecturer.id:
        return ResponseHelper.error('Access denied', 'FORBIDDEN', 403)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'status' in data:
            valid_statuses = ['active', 'closed']
            if data['status'] not in valid_statuses:
                return ResponseHelper.error(f'Invalid status. Must be one of: {", ".join(valid_statuses)}', 'INVALID_DATA', 400)
            session.status = data['status']
        
        db.session.commit()
        return ResponseHelper.success('Session updated', session.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@attendance_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@lecturer_required
def delete_session(session_id):
    """Delete attendance session"""
    session = AttendanceSession.query.get(session_id)
    if not session:
        return ResponseHelper.error('Session not found', 'NOT_FOUND', 404)
    
    # Verify lecturer owns this session
    lecturer = Lecturer.query.filter_by(user_id=get_jwt_identity()).first()
    if not lecturer or session.lecturer_id != lecturer.id:
        return ResponseHelper.error('Access denied', 'FORBIDDEN', 403)
    
    try:
        db.session.delete(session)
        db.session.commit()
        return ResponseHelper.success('Session deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

@attendance_bp.route('/sessions/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_sessions(course_id):
    """Get all sessions for a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        sessions = AttendanceSession.query.filter_by(course_id=course_id).all()
        result = []
        for session in sessions:
            data = session.to_dict()
            lecturer = Lecturer.query.get(session.lecturer_id)
            if lecturer:
                data['lecturer_name'] = f"{lecturer.user.first_name} {lecturer.user.last_name}"
            result.append(data)
        return ResponseHelper.success('Course sessions retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/sessions/lecturer/<int:lecturer_id>', methods=['GET'])
@admin_required
def get_lecturer_sessions(lecturer_id):
    """Get all sessions created by a lecturer"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    try:
        sessions = AttendanceSession.query.filter_by(lecturer_id=lecturer_id).all()
        result = []
        for session in sessions:
            data = session.to_dict()
            course = Course.query.get(session.course_id)
            if course:
                data['course_code'] = course.code
                data['course_name'] = course.name
            result.append(data)
        return ResponseHelper.success('Lecturer sessions retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Attendance Check-in ====================

@attendance_bp.route('/check-in', methods=['POST'])
@student_required
def check_in():
    """Student check-in to attendance session"""
    student_id = get_jwt_identity()
    user = User.query.get(student_id)
    
    # Get student record
    student = Student.query.filter_by(user_id=student_id).first()
    if not student:
        return ResponseHelper.error('Student record not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data or 'session_code' not in data:
        return ResponseHelper.error('session_code required', 'MISSING_FIELD', 400)
    
    try:
        # Find session by code
        session_code = str(data['session_code']).strip()
        session = AttendanceSession.query.filter_by(session_code=session_code).first()
        if not session:
            return ResponseHelper.error('Invalid session code', 'NOT_FOUND', 404)
        
        if session.status != 'active':
            return ResponseHelper.error('Session is not active', 'INVALID_STATE', 400)
        
        # Check if student is enrolled in course
        enrollment = StudentCourse.query.filter_by(
            student_id=student.id,
            course_id=session.course_id,
            is_active=True
        ).first()
        if not enrollment:
            return ResponseHelper.error('Not enrolled in this course', 'FORBIDDEN', 403)
        
        # Check if already checked in
        existing = Attendance.query.filter_by(
            session_id=session.id,
            student_id=student.id
        ).first()
        if existing:
            return ResponseHelper.error('Already checked in', 'DUPLICATE', 400)
        
        # Check if late
        now = datetime.utcnow()
        session_start = datetime.combine(session.session_date, session.start_time)
        late_threshold = session_start + timedelta(minutes=5)  # 5 minute grace period
        
        status = 'present'
        if now > late_threshold:
            status = 'late'
        
        # Record attendance
        attendance = Attendance(
            session_id=session.id,
            student_id=student.id,
            check_in_time=now,
            status=status
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return ResponseHelper.success(
            f'Check-in successful ({status})',
            attendance.to_dict(),
            201
        )
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Check-in failed: {str(e)}', 'CREATE_ERROR', 500)

@attendance_bp.route('/attendance/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session_attendance(session_id):
    """Get all attendance records for a session"""
    session = AttendanceSession.query.get(session_id)
    if not session:
        return ResponseHelper.error('Session not found', 'NOT_FOUND', 404)

    claims = get_jwt()
    if claims.get('role') not in ('admin', 'lecturer'):
        return ResponseHelper.error('Admin or lecturer access required', 'FORBIDDEN', 403)

    if claims.get('role') == 'lecturer':
        lecturer = Lecturer.query.filter_by(user_id=get_jwt_identity()).first()
        if not lecturer or session.lecturer_id != lecturer.id:
            return ResponseHelper.error('You can only view attendance for your sessions', 'FORBIDDEN', 403)
    
    try:
        records = Attendance.query.filter_by(session_id=session_id).all()
        result = []
        for record in records:
            data = record.to_dict()
            student = Student.query.get(record.student_id)
            if student:
                data['student_id_num'] = student.student_id
                data['student_name'] = f"{student.user.first_name} {student.user.last_name}"
            result.append(data)
        return ResponseHelper.success('Session attendance retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/attendance/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student_attendance(student_id):
    """Get all attendance records for a student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        records = Attendance.query.filter_by(student_id=student_id).all()
        result = []
        for record in records:
            data = record.to_dict()
            session = AttendanceSession.query.get(record.session_id)
            course = Course.query.get(session.course_id) if session else None
            if session and course:
                data['course_code'] = course.code
                data['course_name'] = course.name
                data['session_date'] = session.session_date.isoformat()
            result.append(data)
        return ResponseHelper.success('Student attendance retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/attendance/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_attendance(course_id):
    """Get attendance summary for a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        # Get all students enrolled in course
        enrollments = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).all()
        
        result = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if student:
                # Get attendance percentage
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student.id, course_id
                )
                result.append({
                    'student_id': student.id,
                    'student_number': student.student_id,
                    'student_name': f"{student.user.first_name} {student.user.last_name}",
                    'attendance_percentage': percentage
                })
        
        # Sort by attendance percentage
        result.sort(key=lambda x: x['attendance_percentage'])
        
        return ResponseHelper.success('Course attendance summary retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Attendance Warnings ====================

@attendance_bp.route('/warnings', methods=['GET'])
@admin_required
def list_warnings():
    """List all attendance warnings"""
    try:
        warnings = AttendanceWarning.query.all()
        result = []
        for warning in warnings:
            data = warning.to_dict()
            student = Student.query.get(warning.student_id)
            course = Course.query.get(warning.course_id)
            if student and course:
                data['student_id_num'] = student.student_id
                data['student_name'] = f"{student.user.first_name} {student.user.last_name}"
                data['course_code'] = course.code
                data['course_name'] = course.name
            result.append(data)
        return ResponseHelper.success('Warnings retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/warnings/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student_warnings(student_id):
    """Get attendance warnings for a student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        warnings = AttendanceWarning.query.filter_by(student_id=student_id).all()
        result = []
        for warning in warnings:
            data = warning.to_dict()
            course = Course.query.get(warning.course_id)
            if course:
                data['course_code'] = course.code
                data['course_name'] = course.name
            result.append(data)
        return ResponseHelper.success('Student warnings retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/warnings/acknowledge/<int:warning_id>', methods=['PUT'])
def acknowledge_warning(warning_id):
    """Student acknowledges attendance warning"""
    warning = AttendanceWarning.query.get(warning_id)
    if not warning:
        return ResponseHelper.error('Warning not found', 'NOT_FOUND', 404)
    
    try:
        warning.is_acknowledged = True
        db.session.commit()
        return ResponseHelper.success('Warning acknowledged', warning.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@attendance_bp.route('/warnings/generate', methods=['POST'])
@admin_required
def generate_warnings():
    """Generate attendance warnings for all students"""
    data = request.get_json() or {}
    threshold = data.get('threshold', 75)
    critical_threshold = data.get('critical_threshold', 50)
    
    try:
        warnings_created = AttendanceCalculator.create_attendance_warnings(
            threshold=threshold,
            critical_threshold=critical_threshold
        )
        return ResponseHelper.success(
            f'Warnings generated: {warnings_created}',
            {'warnings_created': warnings_created},
            201
        )
    except Exception as e:
        return ResponseHelper.error(f'Generation failed: {str(e)}', 'CREATE_ERROR', 500)

# ==================== QR Code Download ====================

@attendance_bp.route('/qr/<int:session_id>', methods=['GET'])
@admin_required
def download_qr_code(session_id):
    """Download QR code for a session"""
    session = AttendanceSession.query.get(session_id)
    if not session:
        return ResponseHelper.error('Session not found', 'NOT_FOUND', 404)
    
    try:
        # Extract base64 data from data URL
        qr_data = session.qr_code_data
        if qr_data.startswith('data:image/png;base64,'):
            qr_base64 = qr_data.replace('data:image/png;base64,', '')
            import base64
            img_data = base64.b64decode(qr_base64)
            return send_file(
                io.BytesIO(img_data),
                mimetype='image/png',
                as_attachment=True,
                download_name=f'qr_{session.session_code}.png'
            )
        else:
            return ResponseHelper.error('Invalid QR code data', 'INVALID_DATA', 400)
    except Exception as e:
        return ResponseHelper.error(f'Download failed: {str(e)}', 'DOWNLOAD_ERROR', 500)

# ==================== Statistics ====================

@attendance_bp.route('/statistics/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_statistics(course_id):
    """Get attendance statistics for a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        total_sessions = AttendanceSession.query.filter_by(course_id=course_id).count()
        total_students = StudentCourse.query.filter_by(course_id=course_id, is_active=True).count()
        total_attendance = Attendance.query.join(
            AttendanceSession,
            AttendanceSession.id == Attendance.session_id
        ).filter(AttendanceSession.course_id == course_id).count()
        
        stats = {
            'course_id': course_id,
            'course_code': course.code,
            'course_name': course.name,
            'total_sessions': total_sessions,
            'total_students': total_students,
            'total_attendance': total_attendance,
            'average_attendance': (total_attendance / (total_sessions * total_students * 1.0)) * 100 if (total_sessions * total_students) > 0 else 0
        }
        
        return ResponseHelper.success('Course statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@attendance_bp.route('/statistics/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student_statistics(student_id):
    """Get attendance statistics for a student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        summary = AttendanceCalculator.get_student_attendance_summary(student_id)
        
        stats = {
            'student_id': student.id,
            'student_number': student.student_id,
            'student_name': f"{student.user.first_name} {student.user.last_name}",
            'courses': summary,
            'overall_average': sum(c['attendance_percentage'] for c in summary) / len(summary) if summary else 0
        }
        
        return ResponseHelper.success('Student statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)
