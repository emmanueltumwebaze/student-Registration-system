"""Authentication routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from functools import wraps
from app import db
from models import User
from utils import ValidationHelper, ResponseHelper

auth_bp = Blueprint('auth', __name__)

# Role-based access control decorators
def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return ResponseHelper.error('Admin access required', 'FORBIDDEN', 403)
        return fn(*args, **kwargs)
    return wrapper

def lecturer_required(fn):
    """Decorator to require lecturer role"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'lecturer':
            return ResponseHelper.error('Lecturer access required', 'FORBIDDEN', 403)
        return fn(*args, **kwargs)
    return wrapper

def student_required(fn):
    """Decorator to require student role"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'student':
            return ResponseHelper.error('Student access required', 'FORBIDDEN', 403)
        return fn(*args, **kwargs)
    return wrapper

def authenticated_required(fn):
    """Decorator to require authentication"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return ResponseHelper.error('No data provided', 'EMPTY_REQUEST', 400)
    
    # Validate required fields
    required_fields = ['email', 'username', 'password', 'first_name', 'last_name', 'role']
    missing_fields = ValidationHelper.validate_required_fields(data, required_fields)
    if missing_fields:
        return ResponseHelper.error(
            f'Missing required fields: {", ".join(missing_fields)}', 
            'MISSING_FIELDS', 
            400
        )
    
    # Validate email format
    if not ValidationHelper.validate_email(data['email']):
        return ResponseHelper.error('Invalid email format', 'INVALID_EMAIL', 400)
    
    # Validate password strength
    is_valid, password_msg = ValidationHelper.validate_password_strength(data['password'])
    if not is_valid:
        return ResponseHelper.error(password_msg, 'WEAK_PASSWORD', 400)
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return ResponseHelper.error('Email already registered', 'EMAIL_EXISTS', 400)
    
    if User.query.filter_by(username=data['username']).first():
        return ResponseHelper.error('Username already taken', 'USERNAME_EXISTS', 400)
    
    # Validate role
    valid_roles = ['admin', 'lecturer', 'student']
    if data['role'] not in valid_roles:
        return ResponseHelper.error(
            f'Invalid role. Must be one of: {", ".join(valid_roles)}',
            'INVALID_ROLE',
            400
        )
    
    try:
        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return ResponseHelper.success(
            'User registered successfully',
            user.to_dict(),
            201
        )
    except Exception as e:
        db.session.rollback()
        return ResponseHelper.error(f'Registration failed: {str(e)}', 'REGISTRATION_ERROR', 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    admin_email = 'admin@university.edu'
    admin_exists = User.query.filter_by(email=admin_email).first()
    
    if not admin_exists:
        try:
            master_admin = User(
                email=admin_email,
                username='admin',
                first_name='System',
                last_name='Admin',
                role='admin'
            )
            master_admin.set_password('Admin123')
            
            if hasattr(master_admin, 'is_active'):
                master_admin.is_active = True
                
            db.session.add(master_admin)
            db.session.commit()
            print("Master admin seeded dynamically inside login route! 🎉")
        except Exception as e:
            db.session.rollback()
            print(f"Inline seeding failed: {str(e)}")

    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return ResponseHelper.error('Email and password required', 'MISSING_CREDENTIALS', 400)
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return ResponseHelper.error('Invalid email or password', 'INVALID_CREDENTIALS', 401)
    
    if hasattr(user, 'is_active') and not user.is_active:
        return ResponseHelper.error('Account is inactive', 'ACCOUNT_INACTIVE', 403)
    
    try:
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        user_data = user.to_dict()
        
        # Add role-specific information
        if user.role == 'student' and user.student:
            user_data['student_id'] = user.student.student_id
            user_data['program_id'] = user.student.program_id
            user_data['department_id'] = user.student.department_id
        elif user.role == 'lecturer' and user.lecturer:
            user_data['lecturer_id'] = user.lecturer.lecturer_id
            user_data['department_id'] = user.lecturer.department_id
        
        return ResponseHelper.success(
            'Login successful',
            {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_data,
                'expires_in': 86400
            },
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Login failed: {str(e)}', 'LOGIN_ERROR', 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return ResponseHelper.error('User not found', 'USER_NOT_FOUND', 404)
    
    if hasattr(user, 'is_active') and not user.is_active:
        return ResponseHelper.error('Account is inactive', 'ACCOUNT_INACTIVE', 403)
    
    try:
        access_token = create_access_token(identity=user.id)
        return ResponseHelper.success(
            'Token refreshed',
            {
                'access_token': access_token,
                'expires_in': 86400
            },
            200
        )
    except Exception as e:
        return ResponseHelper.error(f'Token refresh failed: {str(e)}', 'REFRESH_ERROR', 500)

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return ResponseHelper.error('User not found', 'USER_NOT_FOUND', 404)
    
    profile = user.to_dict()
    
    if user.role == 'student' and user.student:
        profile['student_id'] = user.student.student_id
        profile['program_id'] = user.student.program_id
        profile['department_id'] = user.student.department_id
    elif user.role == 'lecturer' and user.lecturer:
        profile['lecturer_id'] = user.lecturer.lecturer_id
        profile['department_id'] = user.lecturer.department_id
        
    return ResponseHelper.success('Profile retrieved successfully', profile, 200)
