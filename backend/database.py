"""
Database initialization and utilities
"""
from app import db, create_app
from models import (User, Department, Program, Course, Student, Lecturer, 
                   CourseLecturer, StudentCourse, AttendanceSession, Attendance,
                   AttendanceWarning)
from datetime import datetime, time, timedelta
from werkzeug.security import generate_password_hash

def init_db():
    """Initialize database - create all tables"""
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

def drop_db():
    """Drop all tables - USE WITH CAUTION"""
    app = create_app()
    with app.app_context():
        print("WARNING: This will delete all data!")
        response = input("Are you sure? (type 'yes' to confirm): ")
        if response.lower() == 'yes':
            db.drop_all()
            print("Database tables dropped!")
        else:
            print("Cancelled.")

def seed_sample_data():
    """Seed database with sample data for testing"""
    app = create_app()
    with app.app_context():
        # Check if data already exists
        if User.query.first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding sample data...")

        try:
            # Create admin user
            admin = User(
                email='admin@university.edu',
                username='admin',
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()

            # Create departments
            dept_cs = Department(
                name='Computer Science',
                code='CS',
                description='Department of Computer Science and Engineering'
            )
            dept_eng = Department(
                name='Engineering',
                code='ENG',
                description='Faculty of Engineering'
            )
            dept_bus = Department(
                name='Business',
                code='BUS',
                description='School of Business Administration'
            )
            db.session.add_all([dept_cs, dept_eng, dept_bus])
            db.session.flush()

            # Create programs
            prog_bcs = Program(
                name='Bachelor of Computer Science',
                code='BCS',
                department_id=dept_cs.id,
                duration_years=4
            )
            prog_bse = Program(
                name='Bachelor of Software Engineering',
                code='BSE',
                department_id=dept_cs.id,
                duration_years=4
            )
            prog_be = Program(
                name='Bachelor of Engineering',
                code='BE',
                department_id=dept_eng.id,
                duration_years=4
            )
            db.session.add_all([prog_bcs, prog_bse, prog_be])
            db.session.flush()

            # Create courses
            course_py = Course(
                code='CS101',
                name='Introduction to Python',
                description='Fundamentals of Python programming',
                credits=3,
                program_id=prog_bcs.id
            )
            course_dsa = Course(
                code='CS201',
                name='Data Structures and Algorithms',
                description='Advanced data structures and algorithm design',
                credits=4,
                program_id=prog_bcs.id
            )
            course_db = Course(
                code='CS301',
                name='Database Management',
                description='Relational databases and SQL',
                credits=3,
                program_id=prog_bse.id
            )
            course_web = Course(
                code='CS401',
                name='Web Development',
                description='Full-stack web development',
                credits=4,
                program_id=prog_bse.id
            )
            db.session.add_all([course_py, course_dsa, course_db, course_web])
            db.session.flush()

            # Create lecturer users
            lecturer_user1 = User(
                email='john.smith@university.edu',
                username='jsmith',
                first_name='John',
                last_name='Smith',
                role='lecturer'
            )
            lecturer_user1.set_password('lecturer123')
            db.session.add(lecturer_user1)
            db.session.flush()

            lecturer_user2 = User(
                email='jane.doe@university.edu',
                username='jdoe',
                first_name='Jane',
                last_name='Doe',
                role='lecturer'
            )
            lecturer_user2.set_password('lecturer123')
            db.session.add(lecturer_user2)
            db.session.flush()

            # Create lecturer records
            lecturer1 = Lecturer(
                user_id=lecturer_user1.id,
                lecturer_id='LEC001',
                department_id=dept_cs.id,
                specialization='Python & Web Development'
            )
            lecturer2 = Lecturer(
                user_id=lecturer_user2.id,
                lecturer_id='LEC002',
                department_id=dept_cs.id,
                specialization='Databases & SQL'
            )
            db.session.add_all([lecturer1, lecturer2])
            db.session.flush()

            # Assign lecturers to courses
            assign1 = CourseLecturer(
                course_id=course_py.id,
                lecturer_id=lecturer1.id
            )
            assign2 = CourseLecturer(
                course_id=course_web.id,
                lecturer_id=lecturer1.id
            )
            assign3 = CourseLecturer(
                course_id=course_db.id,
                lecturer_id=lecturer2.id
            )
            db.session.add_all([assign1, assign2, assign3])
            db.session.flush()

            # Create student users
            students_data = [
                ('student1@university.edu', 'student1', 'Alice', 'Johnson'),
                ('student2@university.edu', 'student2', 'Bob', 'Williams'),
                ('student3@university.edu', 'student3', 'Charlie', 'Brown'),
                ('student4@university.edu', 'student4', 'Diana', 'Miller'),
                ('student5@university.edu', 'student5', 'Eve', 'Davis'),
            ]

            student_objects = []
            for i, (email, username, fname, lname) in enumerate(students_data, 1):
                user = User(
                    email=email,
                    username=username,
                    first_name=fname,
                    last_name=lname,
                    role='student'
                )
                user.set_password('student123')
                db.session.add(user)
                db.session.flush()

                student = Student(
                    user_id=user.id,
                    student_id=f'STU{1000+i}',
                    program_id=prog_bcs.id,
                    department_id=dept_cs.id
                )
                db.session.add(student)
                student_objects.append(student)
            
            db.session.flush()

            # Enroll students in courses
            for student in student_objects:
                enrollment1 = StudentCourse(
                    student_id=student.id,
                    course_id=course_py.id
                )
                enrollment2 = StudentCourse(
                    student_id=student.id,
                    course_id=course_dsa.id
                )
                db.session.add_all([enrollment1, enrollment2])
            
            db.session.flush()

            # Create sample attendance sessions
            today = datetime.utcnow().date()
            session1 = AttendanceSession(
                course_id=course_py.id,
                lecturer_id=lecturer1.id,
                session_code='SES001',
                qr_code_data='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw',
                session_date=today,
                start_time=time(9, 0),
                end_time=time(10, 0),
                duration_minutes=60,
                status='closed'
            )
            session2 = AttendanceSession(
                course_id=course_py.id,
                lecturer_id=lecturer1.id,
                session_code='SES002',
                qr_code_data='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw',
                session_date=today - timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                duration_minutes=60,
                status='closed'
            )
            db.session.add_all([session1, session2])
            db.session.flush()

            # Record attendance
            for i, student in enumerate(student_objects):
                # Mark present for session 1
                att1 = Attendance(
                    session_id=session1.id,
                    student_id=student.id,
                    check_in_time=datetime.utcnow(),
                    status='present'
                )
                db.session.add(att1)

                # Mark present for session 2 (except one)
                if i < len(student_objects) - 1:
                    att2 = Attendance(
                        session_id=session2.id,
                        student_id=student.id,
                        check_in_time=datetime.utcnow() - timedelta(days=1),
                        status='present'
                    )
                    db.session.add(att2)

            db.session.commit()
            print("Sample data seeded successfully!")
            print("\nTest Credentials:")
            print("Admin: admin@university.edu / admin123")
            print("Lecturer: john.smith@university.edu / lecturer123")
            print("Student: student1@university.edu / student123")

        except Exception as e:
            db.session.rollback()
            print(f"Error seeding data: {str(e)}")

def get_database_schema():
    """Get database schema information"""
    app = create_app()
    with app.app_context():
        schema_info = {
            'tables': [],
            'relationships': []
        }

        # Get all tables
        for table in db.metadata.tables.values():
            table_info = {
                'name': table.name,
                'columns': []
            }
            for column in table.columns:
                table_info['columns'].append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'unique': column.unique
                })
            schema_info['tables'].append(table_info)

        return schema_info

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'init':
            init_db()
        elif command == 'drop':
            drop_db()
        elif command == 'seed':
            init_db()
            seed_sample_data()
        elif command == 'schema':
            schema = get_database_schema()
            import json
            print(json.dumps(schema, indent=2))
        else:
            print("Usage: python database.py [init|drop|seed|schema]")
    else:
        print("Usage: python database.py [init|drop|seed|schema]")
        print("\nCommands:")
        print("  init   - Initialize database (create tables)")
        print("  drop   - Drop all tables (WARNING: destructive)")
        print("  seed   - Initialize and seed with sample data")
        print("  schema - Display database schema")
