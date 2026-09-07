#!/usr/bin/env python
"""Check student enrollments and sessions"""

from app import create_app
from models import Student, StudentCourse, Course, User, AttendanceSession

app = create_app()
with app.app_context():
    print("=" * 60)
    print("STUDENT ENROLLMENTS")
    print("=" * 60)
    
    students = Student.query.all()
    for student in students:
        user = User.query.get(student.user_id)
        enrollments = StudentCourse.query.filter_by(student_id=student.id, is_active=True).all()
        print(f"\n{user.email}:")
        if enrollments:
            for enrollment in enrollments:
                course = Course.query.get(enrollment.course_id)
                print(f"  ✓ {course.code}: {course.name}")
        else:
            print(f"  ✗ NO ENROLLMENTS")
    
    print("\n" + "=" * 60)
    print("AVAILABLE SESSIONS")
    print("=" * 60)
    
    sessions = AttendanceSession.query.all()
    for i, session in enumerate(sessions, 1):
        course = Course.query.get(session.course_id)
        print(f"\n{i}. Session Code: {session.session_code}")
        print(f"   Course: {course.code}")
        print(f"   Status: {session.status}")
        print(f"   QR Data: {'✓ Yes' if session.qr_code_data else '✗ No'}")

    print("\n" + "=" * 60)

