"""
Authentication and Authorization Middleware
"""
from flask import request, jsonify
from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, create_access_token
from models import User
from utils import ResponseHelper

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ResponseHelper.error('User not found', 'USER_NOT_FOUND', 404)
        
        if not user.is_active:
            return ResponseHelper.error('Account is inactive', 'ACCOUNT_INACTIVE', 403)
        
        return f(*args, **kwargs)
    return decorated

def admin_only(f):
    """Decorator to require admin role"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return ResponseHelper.error('Admin access required', 'FORBIDDEN', 403)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return ResponseHelper.error('User account issue', 'USER_ERROR', 403)
        
        return f(*args, **kwargs)
    return decorated

def lecturer_only(f):
    """Decorator to require lecturer role"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'lecturer':
            return ResponseHelper.error('Lecturer access required', 'FORBIDDEN', 403)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return ResponseHelper.error('User account issue', 'USER_ERROR', 403)
        
        return f(*args, **kwargs)
    return decorated

def student_only(f):
    """Decorator to require student role"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'student':
            return ResponseHelper.error('Student access required', 'FORBIDDEN', 403)
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return ResponseHelper.error('User account issue', 'USER_ERROR', 403)
        
        return f(*args, **kwargs)
    return decorated

def admin_or_self(f):
    """Decorator to allow admin or user accessing own data"""
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Get the target user ID from the URL parameters
        target_user_id = kwargs.get('user_id') or request.args.get('user_id')
        
        # Admin can access anything
        if claims.get('role') == 'admin':
            return f(*args, **kwargs)
        
        # User can only access their own data
        if str(user_id) != str(target_user_id):
            return ResponseHelper.error('Access denied', 'FORBIDDEN', 403)
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return ResponseHelper.error('User account issue', 'USER_ERROR', 403)
        
        return f(*args, **kwargs)
    return decorated

def log_activity(activity_type):
    """Decorator to log user activities (optional)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Log activity here if needed
            # Example: log_to_file(f"User {get_jwt_identity()} performed {activity_type}")
            return f(*args, **kwargs)
        return decorated
    return decorator

class AuthValidator:
    """Utility class for auth validation"""
    
    @staticmethod
    def is_admin(user):
        """Check if user is admin"""
        return user.role == 'admin'
    
    @staticmethod
    def is_lecturer(user):
        """Check if user is lecturer"""
        return user.role == 'lecturer'
    
    @staticmethod
    def is_student(user):
        """Check if user is student"""
        return user.role == 'student'
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users"""
        return AuthValidator.is_admin(user)
    
    @staticmethod
    def can_manage_courses(user):
        """Check if user can manage courses"""
        return AuthValidator.is_admin(user)
    
    @staticmethod
    def can_manage_attendance(user):
        """Check if user can manage attendance"""
        return AuthValidator.is_admin(user) or AuthValidator.is_lecturer(user)
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports"""
        return AuthValidator.is_admin(user) or AuthValidator.is_lecturer(user)

# Export all utilities
__all__ = [
    'token_required',
    'admin_only',
    'lecturer_only',
    'student_only',
    'admin_or_self',
    'log_activity',
    'AuthValidator'
]
