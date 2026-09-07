"""Assignment routes for managing course-lecturer and student-course relationships"""
from flask import Blueprint, request
from routes.auth import admin_required, lecturer_required
from app import db
from models import (CourseLecturer, StudentCourse, Course, Lecturer, Student, 
                   User, Program, Attendance, AttendanceSession)
from utils import ResponseHelper, ValidationHelper
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__)

# ==================== Course-Lecturer Assignments ====================

@assignments_bp.route('/course-lecturers', methods=['GET'])
@admin_required
def list_course_lecturers():
    """List all course-lecturer assignments"""
    try:
        assignments = CourseLecturer.query.all()
        result = []
        for assign in assignments:
            data = assign.to_dict()
            course = Course.query.get(assign.course_id)
            lecturer = Lecturer.query.get(assign.lecturer_id)
            if course and lecturer:
                data['course_code'] = course.code
                data['course_name'] = course.name
                data['lecturer_name'] = f"{lecturer.user.first_name} {lecturer.user.last_name}"
                data['lecturer_id_num'] = lecturer.lecturer_id
            result.append(data)
        return ResponseHelper.success('Course-lecturer assignments retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/course-lecturers', methods=['POST'])
@admin_required
def assign_lecturer_to_course():
    """Assign lecturer to course"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['course_id', 'lecturer_id'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    # Verify course exists
    course = Course.query.get(data['course_id'])
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    # Verify lecturer exists
    lecturer = Lecturer.query.get(data['lecturer_id'])
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    # Check if assignment already exists
    existing = CourseLecturer.query.filter_by(
        course_id=data['course_id'],
        lecturer_id=data['lecturer_id']
    ).first()
    if existing:
        return ResponseHelper.error('Lecturer already assigned to this course', 'DUPLICATE', 400)
    
    try:
        assignment = CourseLecturer(
            course_id=data['course_id'],
            lecturer_id=data['lecturer_id']
        )
        db.session.add(assignment)
        db.session.commit()
        return ResponseHelper.success('Lecturer assigned to course', assignment.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Assignment failed: {str(e)}', 'CREATE_ERROR', 500)

@assignments_bp.route('/course-lecturers/<int:assignment_id>', methods=['GET'])
@admin_required
def get_course_lecturer(assignment_id):
    """Get specific course-lecturer assignment"""
    assign = CourseLecturer.query.get(assignment_id)
    if not assign:
        return ResponseHelper.error('Assignment not found', 'NOT_FOUND', 404)
    
    data = assign.to_dict()
    course = Course.query.get(assign.course_id)
    lecturer = Lecturer.query.get(assign.lecturer_id)
    if course and lecturer:
        data['course_code'] = course.code
        data['course_name'] = course.name
        data['lecturer_name'] = f"{lecturer.user.first_name} {lecturer.user.last_name}"
    
    return ResponseHelper.success('Assignment retrieved', data, 200)

@assignments_bp.route('/course-lecturers/<int:assignment_id>', methods=['PUT'])
@admin_required
def update_course_lecturer(assignment_id):
    """Update course-lecturer assignment"""
    assign = CourseLecturer.query.get(assignment_id)
    if not assign:
        return ResponseHelper.error('Assignment not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'is_active' in data:
            assign.is_active = data['is_active']
        
        db.session.commit()
        return ResponseHelper.success('Assignment updated', assign.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@assignments_bp.route('/course-lecturers/<int:assignment_id>', methods=['DELETE'])
@admin_required
def delete_course_lecturer(assignment_id):
    """Remove lecturer from course"""
    assign = CourseLecturer.query.get(assignment_id)
    if not assign:
        return ResponseHelper.error('Assignment not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(assign)
        db.session.commit()
        return ResponseHelper.success('Assignment deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

@assignments_bp.route('/course-lecturers/lecturer/<int:lecturer_id>', methods=['GET'])
@admin_required
def get_lecturer_courses(lecturer_id):
    """Get all courses assigned to a lecturer"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    try:
        assignments = CourseLecturer.query.filter_by(
            lecturer_id=lecturer_id,
            is_active=True
        ).all()
        
        result = []
        for assign in assignments:
            course = Course.query.get(assign.course_id)
            if course:
                course_data = course.to_dict()
                course_data['assignment_id'] = assign.id
                result.append(course_data)
        
        return ResponseHelper.success('Lecturer courses retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/course-lecturers/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_lecturers(course_id):
    """Get all lecturers assigned to a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        assignments = CourseLecturer.query.filter_by(
            course_id=course_id,
            is_active=True
        ).all()
        
        result = []
        for assign in assignments:
            lecturer = Lecturer.query.get(assign.lecturer_id)
            if lecturer:
                lecturer_data = lecturer.to_dict()
                lecturer_data['assignment_id'] = assign.id
                result.append(lecturer_data)
        
        return ResponseHelper.success('Course lecturers retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Student Course Registrations ====================

@assignments_bp.route('/student-courses', methods=['GET'])
@admin_required
def list_student_courses():
    """List all student course enrollments"""
    try:
        enrollments = StudentCourse.query.all()
        result = []
        for enrollment in enrollments:
            data = enrollment.to_dict()
            student = Student.query.get(enrollment.student_id)
            course = Course.query.get(enrollment.course_id)
            if student and course:
                data['student_id_num'] = student.student_id
                data['student_name'] = f"{student.user.first_name} {student.user.last_name}"
                data['course_code'] = course.code
                data['course_name'] = course.name
            result.append(data)
        return ResponseHelper.success('Student course enrollments retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/student-courses', methods=['POST'])
@admin_required
def enroll_student_in_course():
    """Enroll student in course"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['student_id', 'course_id'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    # Verify student exists
    student = Student.query.get(data['student_id'])
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    # Verify course exists
    course = Course.query.get(data['course_id'])
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    # Check if already enrolled
    existing = StudentCourse.query.filter_by(
        student_id=data['student_id'],
        course_id=data['course_id']
    ).first()
    if existing:
        return ResponseHelper.error('Student already enrolled in this course', 'DUPLICATE', 400)
    
    try:
        enrollment = StudentCourse(
            student_id=data['student_id'],
            course_id=data['course_id']
        )
        db.session.add(enrollment)
        db.session.commit()
        return ResponseHelper.success('Student enrolled in course', enrollment.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Enrollment failed: {str(e)}', 'CREATE_ERROR', 500)

@assignments_bp.route('/student-courses/<int:enrollment_id>', methods=['GET'])
@admin_required
def get_student_course(enrollment_id):
    """Get specific student course enrollment"""
    enrollment = StudentCourse.query.get(enrollment_id)
    if not enrollment:
        return ResponseHelper.error('Enrollment not found', 'NOT_FOUND', 404)
    
    data = enrollment.to_dict()
    student = Student.query.get(enrollment.student_id)
    course = Course.query.get(enrollment.course_id)
    if student and course:
        data['student_id_num'] = student.student_id
        data['student_name'] = f"{student.user.first_name} {student.user.last_name}"
        data['course_code'] = course.code
        data['course_name'] = course.name
    
    return ResponseHelper.success('Enrollment retrieved', data, 200)

@assignments_bp.route('/student-courses/<int:enrollment_id>', methods=['PUT'])
@admin_required
def update_student_course(enrollment_id):
    """Update student course enrollment"""
    enrollment = StudentCourse.query.get(enrollment_id)
    if not enrollment:
        return ResponseHelper.error('Enrollment not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'is_active' in data:
            enrollment.is_active = data['is_active']
        
        db.session.commit()
        return ResponseHelper.success('Enrollment updated', enrollment.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@assignments_bp.route('/student-courses/<int:enrollment_id>', methods=['DELETE'])
@admin_required
def delete_student_course(enrollment_id):
    """Remove student from course"""
    enrollment = StudentCourse.query.get(enrollment_id)
    if not enrollment:
        return ResponseHelper.error('Enrollment not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(enrollment)
        db.session.commit()
        return ResponseHelper.success('Enrollment deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

@assignments_bp.route('/student-courses/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student_enrolled_courses(student_id):
    """Get all courses a student is enrolled in"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        enrollments = StudentCourse.query.filter_by(
            student_id=student_id,
            is_active=True
        ).all()
        
        result = []
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                course_data = course.to_dict()
                course_data['enrollment_id'] = enrollment.id
                result.append(course_data)
        
        return ResponseHelper.success('Student courses retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/student-courses/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_enrolled_students(course_id):
    """Get all students enrolled in a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        enrollments = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).all()
        
        result = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if student:
                student_data = student.to_dict()
                student_data['enrollment_id'] = enrollment.id
                result.append(student_data)
        
        return ResponseHelper.success('Course students retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/bulk-enroll', methods=['POST'])
@admin_required
def bulk_enroll_students():
    """Bulk enroll multiple students in a course"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['course_id', 'student_ids'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    course_id = data['course_id']
    student_ids = data['student_ids']
    
    # Verify course exists
    if not Course.query.get(course_id):
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    if not isinstance(student_ids, list) or len(student_ids) == 0:
        return ResponseHelper.error('student_ids must be a non-empty list', 'INVALID_DATA', 400)
    
    try:
        enrolled = 0
        skipped = 0
        
        for student_id in student_ids:
            # Verify student exists
            student = Student.query.get(student_id)
            if not student:
                skipped += 1
                continue
            
            # Check if already enrolled
            existing = StudentCourse.query.filter_by(
                student_id=student_id,
                course_id=course_id
            ).first()
            if existing:
                skipped += 1
                continue
            
            # Create enrollment
            enrollment = StudentCourse(
                student_id=student_id,
                course_id=course_id
            )
            db.session.add(enrollment)
            enrolled += 1
        
        db.session.commit()
        
        return ResponseHelper.success(
            'Bulk enrollment completed',
            {
                'enrolled': enrolled,
                'skipped': skipped,
                'total': len(student_ids)
            },
            201
        )
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Bulk enrollment failed: {str(e)}', 'CREATE_ERROR', 500)

# ==================== Summary Statistics ====================

@assignments_bp.route('/summary/lecturer/<int:lecturer_id>', methods=['GET'])
@admin_required
def get_lecturer_summary(lecturer_id):
    """Get summary statistics for a lecturer"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    try:
        # Get assigned courses
        course_assignments = CourseLecturer.query.filter_by(
            lecturer_id=lecturer_id,
            is_active=True
        ).count()
        
        # Get total students across all assigned courses
        courses = db.session.query(Course.id).join(
            CourseLecturer,
            CourseLecturer.course_id == Course.id
        ).filter(CourseLecturer.lecturer_id == lecturer_id)
        
        total_students = StudentCourse.query.filter(
            StudentCourse.course_id.in_(db.session.query(Course.id).join(
                CourseLecturer,
                CourseLecturer.course_id == Course.id
            ).filter(CourseLecturer.lecturer_id == lecturer_id)),
            StudentCourse.is_active == True
        ).count()
        
        summary = {
            'lecturer_id': lecturer.lecturer_id,
            'lecturer_name': f"{lecturer.user.first_name} {lecturer.user.last_name}",
            'assigned_courses': course_assignments,
            'total_students': total_students
        }
        
        return ResponseHelper.success('Lecturer summary retrieved', summary, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve summary: {str(e)}', 'QUERY_ERROR', 500)

@assignments_bp.route('/summary/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_summary(course_id):
    """Get summary statistics for a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        assigned_lecturers = CourseLecturer.query.filter_by(
            course_id=course_id,
            is_active=True
        ).count()
        
        enrolled_students = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).count()
        
        summary = {
            'course_id': course.id,
            'course_code': course.code,
            'course_name': course.name,
            'assigned_lecturers': assigned_lecturers,
            'enrolled_students': enrolled_students,
            'credits': course.credits
        }
        
        return ResponseHelper.success('Course summary retrieved', summary, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve summary: {str(e)}', 'QUERY_ERROR', 500)
