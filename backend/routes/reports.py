"""Reporting and Analytics routes"""
from flask import Blueprint, request, send_file
from routes.auth import admin_required, lecturer_required
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from models import (Attendance, AttendanceSession, Course, Student, Lecturer, 
                   User, AttendanceWarning, StudentCourse, CourseLecturer,
                   Program, Department)
from utils import ResponseHelper, AttendanceCalculator, ReportGenerator, DateTimeHelper
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

reports_bp = Blueprint('reports', __name__)

def lecturer_can_access_course(course_id):
    claims = get_jwt()
    if claims.get('role') == 'admin':
        return True
    if claims.get('role') != 'lecturer':
        return False
    lecturer = Lecturer.query.filter_by(user_id=get_jwt_identity()).first()
    return bool(lecturer and CourseLecturer.query.filter_by(
        course_id=course_id,
        lecturer_id=lecturer.id,
        is_active=True
    ).first())

# ==================== Attendance Reports ====================

@reports_bp.route('/attendance/course/<int:course_id>', methods=['GET'])
@admin_required
def get_course_attendance_report(course_id):
    """Get detailed attendance report for a course"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        report = ReportGenerator.generate_attendance_report(course_id, start_date, end_date)
        return ResponseHelper.success('Attendance report retrieved', report, 200)
    except ValueError:
        return ResponseHelper.error('Invalid date format. Use YYYY-MM-DD', 'INVALID_DATA', 400)
    except Exception as e:
        return ResponseHelper.error(f'Failed to generate report: {str(e)}', 'REPORT_ERROR', 500)

@reports_bp.route('/attendance/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student_attendance_report(student_id):
    """Get comprehensive attendance report for a student"""
    student = Student.query.get(student_id)
    if not student:
        return ResponseHelper.error('Student not found', 'NOT_FOUND', 404)
    
    try:
        report = ReportGenerator.generate_student_report(student_id)
        if not report:
            return ResponseHelper.error('Failed to generate report', 'REPORT_ERROR', 500)
        return ResponseHelper.success('Student report retrieved', report, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to generate report: {str(e)}', 'REPORT_ERROR', 500)

@reports_bp.route('/attendance/department/<int:dept_id>', methods=['GET'])
@admin_required
def get_department_attendance_report(dept_id):
    """Get attendance report for an entire department"""
    dept = Department.query.get(dept_id)
    if not dept:
        return ResponseHelper.error('Department not found', 'NOT_FOUND', 404)
    
    try:
        # Get all programs in department
        programs = Program.query.filter_by(department_id=dept_id).all()
        
        # Get all courses in those programs
        courses = Course.query.filter(
            Course.program_id.in_([p.id for p in programs])
        ).all()
        
        dept_stats = {
            'department_id': dept.id,
            'department_name': dept.name,
            'department_code': dept.code,
            'courses': []
        }
        
        total_attendance = 0
        total_students = 0
        
        for course in courses:
            course_stats = {
                'course_id': course.id,
                'course_code': course.code,
                'course_name': course.name,
                'students': []
            }
            
            # Get all students enrolled in this course
            enrollments = StudentCourse.query.filter_by(
                course_id=course.id,
                is_active=True
            ).all()
            
            for enrollment in enrollments:
                student = Student.query.get(enrollment.student_id)
                if student:
                    percentage = AttendanceCalculator.calculate_attendance_percentage(
                        student.id, course.id
                    )
                    course_stats['students'].append({
                        'student_id': student.student_id,
                        'student_name': f"{student.user.first_name} {student.user.last_name}",
                        'attendance_percentage': percentage
                    })
                    total_attendance += percentage
                    total_students += 1
            
            dept_stats['courses'].append(course_stats)
        
        if total_students > 0:
            dept_stats['average_attendance'] = round(total_attendance / total_students, 2)
        else:
            dept_stats['average_attendance'] = 0
        
        return ResponseHelper.success('Department report retrieved', dept_stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to generate report: {str(e)}', 'REPORT_ERROR', 500)

# ==================== Statistics & Analytics ====================

@reports_bp.route('/statistics/summary', methods=['GET'])
@jwt_required()
def get_summary_statistics():
    """Get system-wide attendance statistics"""
    try:
        total_sessions = AttendanceSession.query.count()
        total_attendance = Attendance.query.count()
        total_students = Student.query.count()
        total_courses = Course.query.count()
        
        # Average attendance across all students
        all_students = Student.query.all()
        total_percentage = 0
        for student in all_students:
            summary = AttendanceCalculator.get_student_attendance_summary(student.id)
            if summary:
                avg = sum(c['attendance_percentage'] for c in summary) / len(summary)
                total_percentage += avg
        
        average_attendance = (total_percentage / len(all_students)) if all_students else 0
        
        # Count warnings by level
        low_warnings = AttendanceWarning.query.filter_by(warning_level='low').count()
        critical_warnings = AttendanceWarning.query.filter_by(warning_level='critical').count()
        
        stats = {
            'total_sessions': total_sessions,
            'total_attendance_records': total_attendance,
            'total_students': total_students,
            'total_courses': total_courses,
            'average_attendance': round(average_attendance, 2),
            'warnings': {
                'low': low_warnings,
                'critical': critical_warnings,
                'total': low_warnings + critical_warnings
            }
        }
        
        return ResponseHelper.success('Summary statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

@reports_bp.route('/statistics/by-course', methods=['GET'])
@jwt_required()
def get_statistics_by_course():
    """Get attendance statistics for all courses"""
    try:
        courses = Course.query.all()
        stats = []
        
        for course in courses:
            total_sessions = AttendanceSession.query.filter_by(course_id=course.id).count()
            enrollments = StudentCourse.query.filter_by(course_id=course.id, is_active=True).count()
            
            total_attendance = 0
            student_stats = []
            
            for enrollment in StudentCourse.query.filter_by(course_id=course.id, is_active=True).all():
                student = Student.query.get(enrollment.student_id)
                if student:
                    percentage = AttendanceCalculator.calculate_attendance_percentage(
                        student.id, course.id
                    )
                    total_attendance += percentage
                    student_stats.append({
                        'student_id': student.student_id,
                        'percentage': percentage
                    })
            
            avg_attendance = (total_attendance / len(student_stats)) if student_stats else 0
            
            stats.append({
                'course_id': course.id,
                'course_code': course.code,
                'course_name': course.name,
                'total_sessions': total_sessions,
                'enrolled_students': enrollments,
                'average_attendance': round(avg_attendance, 2),
                'low_attendance_count': sum(1 for s in student_stats if s['percentage'] < 75)
            })
        
        # Sort by lowest average attendance
        stats.sort(key=lambda x: x['average_attendance'])
        
        return ResponseHelper.success('Course statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

@reports_bp.route('/statistics/by-student', methods=['GET'])
@jwt_required()
def get_statistics_by_student():
    """Get attendance statistics for all students"""
    try:
        students = Student.query.all()
        stats = []
        
        for student in students:
            summary = AttendanceCalculator.get_student_attendance_summary(student.id)
            
            if summary:
                avg_attendance = sum(c['attendance_percentage'] for c in summary) / len(summary)
            else:
                avg_attendance = 0
            
            low_courses = sum(1 for c in summary if c['attendance_percentage'] < 75)
            critical_courses = sum(1 for c in summary if c['attendance_percentage'] < 50)
            
            stats.append({
                'student_id': student.student_id,
                'student_name': f"{student.user.first_name} {student.user.last_name}",
                'email': student.user.email,
                'enrolled_courses': len(summary),
                'average_attendance': round(avg_attendance, 2),
                'low_attendance_courses': low_courses,
                'critical_attendance_courses': critical_courses,
                'courses': summary
            })
        
        # Sort by lowest average attendance
        stats.sort(key=lambda x: x['average_attendance'])
        
        return ResponseHelper.success('Student statistics retrieved', stats, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

@reports_bp.route('/statistics/by-date-range', methods=['GET'])
@jwt_required()
def get_statistics_by_date_range():
    """Get attendance statistics for a date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return ResponseHelper.error('start_date and end_date required', 'MISSING_FIELD', 400)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get all sessions in range
        sessions = AttendanceSession.query.filter(
            and_(
                AttendanceSession.session_date >= start,
                AttendanceSession.session_date <= end
            )
        ).all()
        
        # Get attendance records for those sessions
        session_ids = [s.id for s in sessions]
        if not session_ids:
            return ResponseHelper.success('No sessions in date range', {
                'start_date': start_date,
                'end_date': end_date,
                'total_sessions': 0,
                'total_attendance': 0
            }, 200)
        
        records = Attendance.query.filter(
            Attendance.session_id.in_(session_ids)
        ).all()
        
        # Calculate statistics
        present_count = sum(1 for r in records if r.status == 'present')
        late_count = sum(1 for r in records if r.status == 'late')
        
        stats = {
            'start_date': start_date,
            'end_date': end_date,
            'total_sessions': len(sessions),
            'total_attendance_records': len(records),
            'present': present_count,
            'late': late_count,
            'attendance_rate': round((present_count + late_count) / len(records) * 100, 2) if records else 0
        }
        
        return ResponseHelper.success('Date range statistics retrieved', stats, 200)
    except ValueError:
        return ResponseHelper.error('Invalid date format. Use YYYY-MM-DD', 'INVALID_DATA', 400)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve statistics: {str(e)}', 'STATS_ERROR', 500)

# ==================== Low Attendance Tracking ====================

@reports_bp.route('/low-attendance/students', methods=['GET'])
@admin_required
def get_low_attendance_students():
    """Get list of students with low attendance"""
    try:
        threshold = request.args.get('threshold', 75, type=float)
        
        students = Student.query.all()
        low_attendance = []
        
        for student in students:
            summary = AttendanceCalculator.get_student_attendance_summary(student.id)
            
            if summary:
                avg_attendance = sum(c['attendance_percentage'] for c in summary) / len(summary)
            else:
                avg_attendance = 0
            
            if avg_attendance < threshold:
                low_attendance.append({
                    'student_id': student.student_id,
                    'student_name': f"{student.user.first_name} {student.user.last_name}",
                    'email': student.user.email,
                    'average_attendance': round(avg_attendance, 2),
                    'courses': summary
                })
        
        # Sort by lowest attendance
        low_attendance.sort(key=lambda x: x['average_attendance'])
        
        return ResponseHelper.success('Low attendance students retrieved', {
            'threshold': threshold,
            'count': len(low_attendance),
            'students': low_attendance
        }, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@reports_bp.route('/low-attendance/courses', methods=['GET'])
@admin_required
def get_low_attendance_courses():
    """Get list of courses with low average attendance"""
    try:
        threshold = request.args.get('threshold', 75, type=float)
        
        courses = Course.query.all()
        low_attendance_courses = []
        
        for course in courses:
            enrollments = StudentCourse.query.filter_by(
                course_id=course.id,
                is_active=True
            ).all()
            
            if enrollments:
                total = 0
                for enrollment in enrollments:
                    percentage = AttendanceCalculator.calculate_attendance_percentage(
                        enrollment.student_id, course.id
                    )
                    total += percentage
                
                avg = total / len(enrollments)
                
                if avg < threshold:
                    low_attendance_courses.append({
                        'course_id': course.id,
                        'course_code': course.code,
                        'course_name': course.name,
                        'enrolled_students': len(enrollments),
                        'average_attendance': round(avg, 2)
                    })
        
        # Sort by lowest attendance
        low_attendance_courses.sort(key=lambda x: x['average_attendance'])
        
        return ResponseHelper.success('Low attendance courses retrieved', {
            'threshold': threshold,
            'count': len(low_attendance_courses),
            'courses': low_attendance_courses
        }, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

@reports_bp.route('/low-attendance/warnings', methods=['GET'])
@admin_required
def get_low_attendance_warnings():
    """Get all low attendance warnings"""
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
                data['student_email'] = student.user.email
                data['course_code'] = course.code
                data['course_name'] = course.name
            
            result.append(data)
        
        # Sort by warning level (critical first) then by attendance percentage
        result.sort(key=lambda x: (x['warning_level'] != 'critical', x['attendance_percentage']))
        
        return ResponseHelper.success('Low attendance warnings retrieved', result, 200)
    except Exception as e:
        return ResponseHelper.error(f'Failed to retrieve: {str(e)}', 'QUERY_ERROR', 500)

# ==================== Report Export ====================

@reports_bp.route('/export/attendance-csv/<int:course_id>', methods=['GET'])
@jwt_required()
def export_attendance_csv(course_id):
    """Export attendance report as CSV"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    if not lecturer_can_access_course(course_id):
        return ResponseHelper.error('You are not assigned to this course', 'FORBIDDEN', 403)
    
    try:
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Course', course.name])
        writer.writerow(['Code', course.code])
        writer.writerow(['Generated', DateTimeHelper.get_now().isoformat()])
        writer.writerow([])
        writer.writerow(['Student ID', 'Student Name', 'Email', 'Attendance %', 'Status'])
        
        # Get attendance data
        enrollments = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).all()
        
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if student:
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student.id, course_id
                )
                
                # Determine status
                if percentage >= 75:
                    status = 'Good'
                elif percentage >= 50:
                    status = 'Low'
                else:
                    status = 'Critical'
                
                writer.writerow([
                    student.student_id,
                    f"{student.user.first_name} {student.user.last_name}",
                    student.user.email,
                    f"{percentage:.2f}%",
                    status
                ])
        
        # Prepare response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'attendance_{course.code}_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return ResponseHelper.error(f'Export failed: {str(e)}', 'EXPORT_ERROR', 500)

@reports_bp.route('/export/attendance-pdf/<int:course_id>', methods=['GET'])
@jwt_required()
def export_attendance_pdf(course_id):
    """Export attendance report as PDF"""
    course = Course.query.get(course_id)
    if not course:
        return ResponseHelper.error('Course not found', 'NOT_FOUND', 404)
    if not lecturer_can_access_course(course_id):
        return ResponseHelper.error('You are not assigned to this course', 'FORBIDDEN', 403)
    
    try:
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph('Attendance Report', title_style))
        
        # Add course info
        info_data = [
            ['Course Name:', course.name],
            ['Course Code:', course.code],
            ['Generated:', DateTimeHelper.get_now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        info_table = Table(info_data)
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Get attendance data
        enrollments = StudentCourse.query.filter_by(
            course_id=course_id,
            is_active=True
        ).all()
        
        table_data = [['Student ID', 'Name', 'Email', 'Attendance %', 'Status']]
        
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if student:
                percentage = AttendanceCalculator.calculate_attendance_percentage(
                    student.id, course_id
                )
                
                if percentage >= 75:
                    status = 'Good'
                elif percentage >= 50:
                    status = 'Low'
                else:
                    status = 'Critical'
                
                table_data.append([
                    student.student_id,
                    f"{student.user.first_name} {student.user.last_name}",
                    student.user.email,
                    f"{percentage:.2f}%",
                    status
                ])
        
        # Create attendance table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        story.append(table)
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'attendance_{course.code}_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        return ResponseHelper.error(f'Export failed: {str(e)}', 'EXPORT_ERROR', 500)
