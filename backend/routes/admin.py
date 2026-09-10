"""Admin routes for system management"""
from flask import Blueprint, request, jsonify
from routes.auth import admin_required
from app import db
from models import (User, Student, Lecturer, Department, Program, Course, 
                   CourseLecturer, StudentCourse, Attendance, AttendanceWarning)
from utils import ResponseHelper, ValidationHelper
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# ==================== Department Management ====================

@admin_bp.route('/departments', methods=['GET'])
@admin_required
def list_departments():
    """List all departments"""
    try:
        departments = Department.query.all()
        return ResponseHelper.success(
            'Departments retrieved',
            [d.to_dict() for d in departments],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve departments: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/departments', methods=['POST'])
@admin_required
def create_department():
    """Create new department"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['name', 'code'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    if Department.query.filter_by(code=data['code']).first():
        return ResponseHelper.error('Department code already exists', 'CODE_EXISTS', 400)
    
    try:
        dept = Department(
            name=data['name'],
            code=data['code'],
            description=data.get('description', '')
        )
        db.session.add(dept)
        db.session.flush()
        response_data = dept.to_dict()
        db.session.commit()
        return ResponseHelper.success('Department created', response_data, 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Creation failed: {str(e)}', 'CREATE_ERROR', 500)

@admin_bp.route('/departments/<int:dept_id>', methods=['GET'])
@admin_required
def get_department(dept_id):
    """Get department details"""
    dept = Department.query.get(dept_id)
    if not dept:
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('Department retrieved', dept.to_dict(), 200)

@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@admin_required
def update_department(dept_id):
    """Update department"""
    dept = Department.query.get(dept_id)
    if not dept:
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'name' in data and data['name']:
            dept.name = data['name']
        if 'code' in data and data['code']:
            if Department.query.filter_by(code=data['code']).filter(Department.id != dept_id).first():
                return ResponseHelper.error('Department code already exists', 'CODE_EXISTS', 400)
            dept.code = data['code']
        if 'description' in data:
            dept.description = data['description']
        
        db.session.commit()
        return ResponseHelper.success('Department updated', dept.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@admin_required
def delete_department(dept_id):
    """Delete department"""
    dept = Department.query.get(dept_id)
    if not dept:
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(dept)
        db.session.commit()
        return ResponseHelper.success('Department deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== Program Management ====================

@admin_bp.route('/programs', methods=['GET'])
@admin_required
def list_programs():
    """List all programs"""
    try:
        programs = Program.query.all()
        return ResponseHelper.success(
            'Programs retrieved',
            [p.to_dict() for p in programs],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve programs: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/programs', methods=['POST'])
@admin_required
def create_program():
    """Create new program"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['name', 'code', 'department_id'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    if Program.query.filter_by(code=data['code']).first():
        return ResponseHelper.error('Program code already exists', 'CODE_EXISTS', 400)
    
    if not Department.query.get(data['department_id']):
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    try:
        program = Program(
            name=data['name'],
            code=data['code'],
            department_id=data['department_id'],
            duration_years=data.get('duration_years', 4),
            description=data.get('description', '')
        )
        db.session.add(program)
        db.session.flush()
        response_data = program.to_dict()
        db.session.commit()
        return ResponseHelper.success('Program created', response_data, 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Creation failed: {str(e)}', 'CREATE_ERROR', 500)

@admin_bp.route('/programs/<int:prog_id>', methods=['GET'])
@admin_required
def get_program(prog_id):
    """Get program details"""
    program = Program.query.get(prog_id)
    if not program:
        return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('Program retrieved', program.to_dict(), 200)

@admin_bp.route('/programs/<int:prog_id>', methods=['PUT'])
@admin_required
def update_program(prog_id):
    """Update program"""
    program = Program.query.get(prog_id)
    if not program:
        return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'name' in data and data['name']:
            program.name = data['name']
        if 'code' in data and data['code']:
            if Program.query.filter_by(code=data['code']).filter(Program.id != prog_id).first():
                return ResponseHelper.error('Program code already exists', 'CODE_EXISTS', 400)
            program.code = data['code']
        if 'duration_years' in data:
            program.duration_years = data['duration_years']
        if 'description' in data:
            program.description = data['description']
        
        db.session.commit()
        return ResponseHelper.success('Program updated', program.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/programs/<int:prog_id>', methods=['DELETE'])
@admin_required
def delete_program(prog_id):
    """Delete program"""
    program = Program.query.get(prog_id)
    if not program:
        return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(program)
        db.session.commit()
        return ResponseHelper.success('Program deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== Course Management ====================

@admin_bp.route('/courses', methods=['GET'])
@admin_required
def list_courses():
    """List all courses"""
    try:
        courses = Course.query.all()
        return ResponseHelper.success(
            'Courses retrieved',
            [c.to_dict() for c in courses],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve courses: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/courses', methods=['POST'])
@admin_required
def create_course():
    """Create new course"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    missing = ValidationHelper.validate_required_fields(data, ['code', 'name', 'program_id'])
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    if Course.query.filter_by(code=data['code']).first():
        return ResponseHelper.error('Course code already exists', 'CODE_EXISTS', 400)
    
    if not Program.query.get(data['program_id']):
        return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
    
    try:
        course = Course(
            code=data['code'],
            name=data['name'],
            program_id=data['program_id'],
            credits=data.get('credits', 3),
            description=data.get('description', '')
        )
        db.session.add(course)
        db.session.flush()
        response_data = course.to_dict()
        db.session.commit()
        return ResponseHelper.success('Course created', response_data, 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Creation failed: {str(e)}', 'CREATE_ERROR', 500)

@admin_bp.route('/courses/<int:course_id>', methods=['GET'])
@admin_required
def get_course(course_id):
    """Get course details"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('Course retrieved', course.to_dict(), 200)

@admin_bp.route('/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    """Update course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'name' in data and data['name']:
            course.name = data['name']
        if 'code' in data and data['code']:
            if Course.query.filter_by(code=data['code']).filter(Course.id != course_id).first():
                return ResponseHelper.error('Course code already exists', 'CODE_EXISTS', 400)
            course.code = data['code']
        if 'credits' in data:
            course.credits = data['credits']
        if 'description' in data:
            course.description = data['description']
        if 'is_active' in data:
            course.is_active = data['is_active']
        
        db.session.commit()
        return ResponseHelper.success('Course updated', course.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(course)
        db.session.commit()
        return ResponseHelper.success('Course deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== Student Management ====================

@admin_bp.route('/students', methods=['GET'])
@admin_required
def list_students():
    """List all students"""
    try:
        students = Student.query.all()
        return ResponseHelper.success(
            'Students retrieved',
            [s.to_dict() for s in students],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve students: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/students', methods=['POST'])
@admin_required
def register_student():
    """Register new student"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    required = ['email', 'username', 'password', 'first_name', 'last_name', 'student_id', 'program_id', 'department_id']
    missing = ValidationHelper.validate_required_fields(data, required)
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    # Validate email
    if not ValidationHelper.validate_email(data['email']):
        return ResponseHelper.error('Invalid email format', 'INVALID_EMAIL', 400)
    
    # Check duplicates
    if User.query.filter_by(email=data['email']).first():
        return ResponseHelper.error('Email already exists', 'EMAIL_EXISTS', 400)
    if User.query.filter_by(username=data['username']).first():
        return ResponseHelper.error('Username already exists', 'USERNAME_EXISTS', 400)
    if Student.query.filter_by(student_id=data['student_id']).first():
        return ResponseHelper.error('Student ID already exists', 'ID_EXISTS', 400)

    is_valid, msg = ValidationHelper.validate_password_strength(data['password'])
    if not is_valid:
        return ResponseHelper.error(msg, 'WEAK_PASSWORD', 400)
    
    # Verify program and department exist
    if not Program.query.get(data['program_id']):
        return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
    if not Department.query.get(data['department_id']):
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    try:
        # Create user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='student'
        )
        user.set_password(data['password'])
        user.must_change_password = True
        db.session.add(user)
        db.session.flush()
        
        # Create student record
        student = Student(
            user_id=user.id,
            student_id=data['student_id'],
            program_id=data['program_id'],
            department_id=data['department_id']
        )
        db.session.add(student)
        db.session.flush()
        response_data = student.to_dict()
        db.session.commit()
        return ResponseHelper.success('Student registered. The temporary password must be changed at first login.', response_data, 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Registration failed: {str(e)}', 'CREATE_ERROR', 500)

@admin_bp.route('/students/<int:student_id>', methods=['GET'])
@admin_required
def get_student(student_id):
    """Get student details"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('Student retrieved', student.to_dict(), 200)

@admin_bp.route('/students/<int:student_id>', methods=['PUT'])
@admin_required
def update_student(student_id):
    """Update student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'is_active' in data:
            student.is_active = data['is_active']
        if 'program_id' in data:
            if not Program.query.get(data['program_id']):
                return ResponseHelper.error('Program not found', 'NOT_FOUND', 404)
            student.program_id = data['program_id']
        if 'department_id' in data:
            if not Department.query.get(data['department_id']):
                return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
            student.department_id = data['department_id']
        
        db.session.commit()
        return ResponseHelper.success('Student updated', student.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """Delete student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(student)
        db.session.commit()
        return ResponseHelper.success('Student deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== Lecturer Management ====================

@admin_bp.route('/lecturers', methods=['GET'])
@admin_required
def list_lecturers():
    """List all lecturers"""
    try:
        lecturers = Lecturer.query.all()
        return ResponseHelper.success(
            'Lecturers retrieved',
            [l.to_dict() for l in lecturers],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve lecturers: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/lecturers', methods=['POST'])
@admin_required
def register_lecturer():
    """Register new lecturer"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    required = ['email', 'username', 'password', 'first_name', 'last_name', 'lecturer_id', 'department_id']
    missing = ValidationHelper.validate_required_fields(data, required)
    if missing:
        return ResponseHelper.error(f'Missing fields: {", ".join(missing)}', 'MISSING_FIELDS', 400)
    
    # Validate email
    if not ValidationHelper.validate_email(data['email']):
        return ResponseHelper.error('Invalid email format', 'INVALID_EMAIL', 400)
    
    # Check duplicates
    if User.query.filter_by(email=data['email']).first():
        return ResponseHelper.error('Email already exists', 'EMAIL_EXISTS', 400)
    if User.query.filter_by(username=data['username']).first():
        return ResponseHelper.error('Username already exists', 'USERNAME_EXISTS', 400)
    if Lecturer.query.filter_by(lecturer_id=data['lecturer_id']).first():
        return ResponseHelper.error('Lecturer ID already exists', 'ID_EXISTS', 400)

    is_valid, msg = ValidationHelper.validate_password_strength(data['password'])
    if not is_valid:
        return ResponseHelper.error(msg, 'WEAK_PASSWORD', 400)
    
    # Verify department exists
    if not Department.query.get(data['department_id']):
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    try:
        # Create user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='lecturer'
        )
        user.set_password(data['password'])
        user.must_change_password = True
        db.session.add(user)
        db.session.flush()
        
        # Create lecturer record
        lecturer = Lecturer(
            user_id=user.id,
            lecturer_id=data['lecturer_id'],
            department_id=data['department_id'],
            specialization=data.get('specialization', '')
        )
        db.session.add(lecturer)
        db.session.flush()
        response_data = {
            'id': lecturer.id,
            'user_id': user.id,
            'lecturer_id': lecturer.lecturer_id,
            'department_id': lecturer.department_id,
            'specialization': lecturer.specialization,
            'is_active': lecturer.is_active
        }
        db.session.commit()
        
        return ResponseHelper.success('Lecturer registered. The temporary password must be changed at first login.', response_data, 201)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Registration failed: {str(e)}', 'CREATE_ERROR', 500)

@admin_bp.route('/lecturers/<int:lecturer_id>', methods=['GET'])
@admin_required
def get_lecturer(lecturer_id):
    """Get lecturer details"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('Lecturer retrieved', lecturer.to_dict(), 200)

@admin_bp.route('/lecturers/<int:lecturer_id>', methods=['PUT'])
@admin_required
def update_lecturer(lecturer_id):
    """Update lecturer"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    try:
        if 'specialization' in data:
            lecturer.specialization = data['specialization']
        if 'is_active' in data:
            lecturer.is_active = data['is_active']
        if 'department_id' in data:
            if not Department.query.get(data['department_id']):
                return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
            lecturer.department_id = data['department_id']
        
        db.session.commit()
        return ResponseHelper.success('Lecturer updated', lecturer.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/lecturers/<int:lecturer_id>', methods=['DELETE'])
@admin_required
def delete_lecturer(lecturer_id):
    """Delete lecturer"""
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return ResponseHelper.error('Lecturer not found', 'NOT_FOUND', 404)
    
    try:
        db.session.delete(lecturer)
        db.session.commit()
        return ResponseHelper.success('Lecturer deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== User Management ====================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users"""
    try:
        users = User.query.all()
        return ResponseHelper.success(
            'Users retrieved',
            [u.to_dict() for u in users],
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve users: {str(e)}', 'QUERY_ERROR', 500)

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get user details"""
    user = User.query.get(user_id)
    if not user:
        return ResponseHelper.error('User not found', 'NOT_FOUND', 404)
    return ResponseHelper.success('User retrieved', user.to_dict(), 200)

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get(user_id)
    if not user:
        return ResponseHelper.error('User not found', 'NOT_FOUND', 404)
    
    data = request.get_json()
    if not data or 'is_active' not in data:
        return ResponseHelper.error('is_active field required', 'MISSING_FIELD', 400)
    
    try:
        user.is_active = data['is_active']
        db.session.commit()
        return ResponseHelper.success('User status updated', user.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Update failed: {str(e)}', 'UPDATE_ERROR', 500)

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get(user_id)
    if not user:
        return ResponseHelper.error('User not found', 'NOT_FOUND', 404)
    
    # Prevent deleting self
    from flask_jwt_extended import get_jwt_identity
    current_user_id = get_jwt_identity()
    if current_user_id == user_id:
        return ResponseHelper.error('Cannot delete your own account', 'FORBIDDEN', 403)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return ResponseHelper.success('User deleted', None, 200)
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Deletion failed: {str(e)}', 'DELETE_ERROR', 500)

# ==================== Statistics ====================

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """Get system statistics"""
    try:
        stats = {
            'total_users': User.query.count(),
            'total_students': Student.query.count(),
            'total_lecturers': Lecturer.query.count(),
            'total_departments': Department.query.count(),
            'total_programs': Program.query.count(),
            'total_courses': Course.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'active_students': Student.query.filter_by(is_active=True).count(),
            'active_lecturers': Lecturer.query.filter_by(is_active=True).count(),
        }
        return ResponseHelper.success('Statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'QUERY_ERROR', 500)
