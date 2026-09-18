"""
Student Attendance System - Flask Application
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db, jwt
from dotenv import load_dotenv
from datetime import timedelta
from sqlalchemy import inspect, text

# Load environment variables
load_dotenv()

# Initialize extensions (must be before importing models)


def seed_default_data():
    """Create the minimum required default records for a fresh database."""
    from models import User, Department, Program

    admin = User.query.filter_by(email='admin@university.edu').first()
    if not admin:
        admin = User(
            email='admin@university.edu',
            username='admin',
            first_name='System',
            last_name='Admin',
            role='admin'
        )
        admin.set_password('Admin123')
        admin.is_active = True
        db.session.add(admin)
        db.session.flush()

    department = Department.query.filter_by(code='CS').first()
    if not department:
        department = Department(
            name='Computer Science',
            code='CS',
            description='Default department for newly created accounts'
        )
        db.session.add(department)
        db.session.flush()

    program = Program.query.filter_by(code='BCS').first()
    if not program:
        program = Program(
            name='Bachelor of Computer Science',
            code='BCS',
            department_id=department.id,
            duration_years=4,
            description='Default program used for registration tests and setup'
        )
        db.session.add(program)

    db.session.commit()


def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name or os.getenv('FLASK_ENV', 'development')])

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "connect_args": {"keepalives": 1, "keepalives_idle": 30}
    }
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
        }}
    )

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # JWT error handlers
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        from models import User
        return User.query.get(identity)
    
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        from models import User
        user = User.query.get(identity)
        if user:
            return {
                'role': user.role,
                'email': user.email,
                'is_active': user.is_active
            }
        return {}
    
    # Register blueprints after app context
    with app.app_context():
        # Import models to register them
        import models  # noqa
        from routes import auth_bp, admin_bp, lecturer_bp, student_bp, attendance_bp, assignments_bp, reports_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
        app.register_blueprint(lecturer_bp, url_prefix='/api/lecturer')
        app.register_blueprint(student_bp, url_prefix='/api/student')
        app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
        app.register_blueprint(reports_bp, url_prefix='/api/reports')
        
        # Create tables
        db.create_all()

        # Add new user fields to an existing PostgreSQL/SQLite database.
        user_columns = {column['name'] for column in inspect(db.engine).get_columns('users')}
        if 'must_change_password' not in user_columns:
            db.session.execute(text(
                'ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE'
            ))
            db.session.commit()

        seed_default_data()
    
    return app

if __name__ == '__main__':
    app = create_app('production')
    with app.app_context():
        db.create_all()


        # Add this block right here to automatically insert your Admin profile:
        from models import User
        from werkzeug.security import generate_password_hash

        # Change this email address to whatever admin account you want to use!
        admin_email = 'admin@university.edu' 
        
        admin_exists = User.query.filter_by(email=admin_email).first()
        if not admin_exists:

            # Modify these placeholder variables to match your exact User model column strings:
            master_admin = User(
                email='admin_email',
                password=generate_password_hash('Admin123'), # Choose your password here
                role='admin',
                first_name='System',
                last_name='Admin',
                is_active=True
            )
            db.session.add(master_admin)
            db.session.commit()
            print("Master administrator account successfully seeded into live database! 🎉")

        app.run(debug=True, host='0.0.0.0', port=5000)

        
    
    
