/**
 * Lecturer Dashboard Manager
 * Handles lecturer courses, sessions, attendance viewing, and report generation
 */

class LecturerDashboard {
    constructor() {
        this.api = api;
        this.currentUser = null;
        this.courses = [];
        this.sessions = [];
        this.currentSession = null;
        
        this.init();
    }

    async init() {
        // Check authentication
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        
        if (!token || !userStr) {
            window.location.href = '../pages/login.html';
            return;
        }

        const user = JSON.parse(userStr);
        if (user.role !== 'lecturer') {
            window.location.href = '../pages/login.html';
            return;
        }

        // Verify token is still valid
        try {
            await this.api.getProfile();
        } catch (error) {
            console.error('Token validation failed:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '../pages/login.html';
            return;
        }

        // Get current user info
        try {
            const response = await this.api.getProfile();
            if (response && response.data) {
                this.currentUser = response.data;
                this.updateUserInfo();
                this.setupEventListeners();
                await this.loadData();
            } else {
                this.showError('Failed to load user profile');
            }
        } catch (error) {
            console.error('Init error:', error);
            this.showError('Error initializing dashboard');
        }
    }

    updateUserInfo() {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.textContent = `${this.currentUser.first_name} ${this.currentUser.last_name}`;
        }
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => this.switchTab(e));
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());

        // Session form
        document.getElementById('sessionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSession();
        });

        // Course filters
        document.getElementById('courseSelectAttendance').addEventListener('change', () => {
            this.loadAttendanceForCourse();
        });

        document.getElementById('sessionSelectAttendance').addEventListener('change', () => {
            this.loadAttendanceForSession();
        });

        // Report course selects
        document.getElementById('reportCourse').addEventListener('change', () => {
            this.enableReportButtons();
        });

        document.getElementById('statsCourse').addEventListener('change', () => {
            this.enableStatsButton();
        });

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeQRModal();
        });

        document.getElementById('qrModal').addEventListener('click', (e) => {
            if (e.target.id === 'qrModal') {
                this.closeQRModal();
            }
        });
    }

    async loadData() {
        try {
            await this.loadCourses();
            await this.loadSessions();
            await this.loadStatistics();
        } catch (error) {
            console.error('Load data error:', error);
        }
    }

    async loadCourses() {
        try {
            const response = await this.api.getLecturerCourses();
            if (response) {
                this.courses = response.data || [];
                this.renderCourses();
                this.populateSelectDropdowns();
            }
        } catch (error) {
            console.error('Load courses error:', error);
        }
    }

    renderCourses() {
        const coursesGrid = document.getElementById('coursesGrid');
        
        if (!this.courses || this.courses.length === 0) {
            coursesGrid.innerHTML = '<div class="empty-state">No courses assigned</div>';
            return;
        }

        coursesGrid.innerHTML = this.courses.map(course => `
            <div class="course-card">
                <div class="course-code">${course.course_code}</div>
                <div class="course-name">${course.course_name}</div>
                
                <div class="course-stats">
                    <div class="course-stat">
                        <div class="course-stat-value">${course.enrolled_students || 0}</div>
                        <div class="course-stat-label">Students</div>
                    </div>
                    <div class="course-stat">
                        <div class="course-stat-value">${course.total_sessions || 0}</div>
                        <div class="course-stat-label">Sessions</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    populateSelectDropdowns() {
        const selects = ['sessionCourse', 'courseSelectAttendance', 'reportCourse', 'statsCourse'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Select a course...</option>' +
                    this.courses.map(c => `<option value="${c.course_id}">${c.course_code} - ${c.course_name}</option>`).join('');
                select.value = currentValue;
            }
        });
    }

    async loadSessions() {
        try {
            const response = await this.api.getLecturerSessions();
            if (response) {
                this.sessions = response.data || [];
                this.renderSessions();
            }
        } catch (error) {
            console.error('Load sessions error:', error);
        }
    }

    renderSessions() {
        const sessionsList = document.getElementById('sessionsList');
        
        if (!this.sessions || this.sessions.length === 0) {
            sessionsList.innerHTML = '<div class="empty-state">No sessions created yet</div>';
            return;
        }

        sessionsList.innerHTML = this.sessions.map(session => {
            const expired = this.isSessionExpired(session);
            return `
            <div class="session-card">
                <div class="session-header">
                    <div class="session-title">${session.course_code}</div>
                    <div class="session-status-badge ${session.status === 'closed' ? 'closed' : ''}">
                        ${session.status}
                    </div>
                </div>
                
                <div class="session-info">
                    <div>📅 ${new Date(session.session_date).toLocaleDateString()}</div>
                    <div>⏰ ${session.start_time} - ${session.end_time}</div>
                    <div>📝 Code: ${session.session_code}</div>
                </div>
                
                <div class="session-actions">
                    ${session.status === 'active' && !expired ? `
                        <button class="session-btn session-btn-primary" onclick="lecturer.showQRCode(${session.id})">
                            QR Code
                        </button>
                        <button class="session-btn session-btn-secondary" onclick="lecturer.closeSession(${session.id})">
                            Close
                        </button>
                    ` : `
                        <button class="session-btn session-btn-secondary" onclick="lecturer.viewSessionAttendance(${session.id})">
                            View
                        </button>
                        <button class="session-btn session-btn-secondary" onclick="lecturer.deleteSession(${session.id})">
                            Delete
                        </button>
                    `}
                </div>
            </div>
        `;
        }).join('');
    }

    isSessionExpired(session) {
        const end = new Date(`${session.session_date}T${session.end_time}`);
        return session.status === 'closed' || end.getTime() < Date.now();
    }

    async createSession() {
        const courseId = document.getElementById('sessionCourse').value;
        const sessionDate = document.getElementById('sessionDate').value;
        const startTime = document.getElementById('startTime').value;
        const endTime = document.getElementById('endTime').value;

        if (!courseId || !sessionDate || !startTime || !endTime) {
            this.showError('Please fill all fields');
            return;
        }

        try {
            const response = await this.api.createSession({
                course_id: parseInt(courseId),
                session_date: sessionDate,
                start_time: startTime,
                end_time: endTime
            });

            if (response && response.data) {
                this.showSuccess('Session created successfully');
                document.getElementById('sessionForm').reset();
                await this.loadSessions();
            } else {
                this.showError('Failed to create session');
            }
        } catch (error) {
            console.error('Create session error:', error);
            this.showError('Error creating session');
        }
    }

    async showQRCode(sessionId) {
        try {
            const session = this.sessions.find(s => s.id === sessionId);
            if (!session) return;

            document.getElementById('qrImage').src = session.qr_code_data;
            document.getElementById('sessionCodeDisplay').textContent = session.session_code;
            
            const course = this.courses.find(c => c.course_id === session.course_id);
            document.getElementById('courseDisplay').textContent = course ? `${course.course_code} - ${course.course_name}` : 'N/A';
            
            const dateTime = `${new Date(session.session_date).toLocaleDateString()} ${session.start_time}`;
            document.getElementById('dateTimeDisplay').textContent = dateTime;

            this.currentSession = session;
            document.getElementById('qrModal').classList.add('active');
        } catch (error) {
            console.error('Show QR error:', error);
        }
    }

    downloadQR() {
        if (!this.currentSession) return;
        
        const link = document.createElement('a');
        link.href = this.currentSession.qr_code_data;
        link.download = `qr_${this.currentSession.session_code}.png`;
        link.click();
    }

    closeQRModal() {
        document.getElementById('qrModal').classList.remove('active');
    }

    async closeSession(sessionId) {
        if (!confirm('Close this session? Students will no longer be able to check in.')) {
            return;
        }

        try {
            const response = await this.api.updateSession(sessionId, { status: 'closed' });
            if (response && response.data) {
                this.showSuccess('Session closed');
                await this.loadSessions();
            }
        } catch (error) {
            console.error('Close session error:', error);
            this.showError('Error closing session');
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('Delete this expired session? Attendance records for this session will also be deleted.')) {
            return;
        }

        try {
            await this.api.deleteSession(sessionId);
            this.showSuccess('Session deleted');
            await this.loadSessions();
        } catch (error) {
            console.error('Delete session error:', error);
            this.showError(error.message || 'Error deleting session');
        }
    }

    async loadAttendanceForCourse() {
        const courseId = document.getElementById('courseSelectAttendance').value;
        if (!courseId) {
            document.getElementById('attendanceTableBody').innerHTML = 
                '<tr class="empty-state"><td colspan="4">Select a course</td></tr>';
            return;
        }

        // Populate sessions for this course
        const sessionSelect = document.getElementById('sessionSelectAttendance');
        const courseSessions = this.sessions.filter(s => s.course_id === parseInt(courseId));
        
        sessionSelect.innerHTML = '<option value="">Select a session...</option>' +
            courseSessions.map(s => `<option value="${s.id}">${s.session_code} - ${s.session_date}</option>`).join('');
    }

    async loadAttendanceForSession() {
        const sessionId = document.getElementById('sessionSelectAttendance').value;
        if (!sessionId) {
            document.getElementById('attendanceTableBody').innerHTML = 
                '<tr class="empty-state"><td colspan="4">Select a session</td></tr>';
            return;
        }

        try {
            const response = await this.api.getSessionAttendance(parseInt(sessionId));
            if (response && response.data) {
                this.renderAttendanceTable(response.data);
            }
        } catch (error) {
            console.error('Load attendance error:', error);
            this.showError(error.message || 'Unable to load attendance records');
        }
    }

    renderAttendanceTable(records) {
        const tbody = document.getElementById('attendanceTableBody');
        
        if (!records || records.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="4">No attendance records</td></tr>';
            return;
        }

        tbody.innerHTML = records.map(record => `
            <tr>
                <td>${record.student_id_num || 'N/A'}</td>
                <td>${record.student_name || 'N/A'}</td>
                <td>${new Date(record.check_in_time).toLocaleTimeString()}</td>
                <td>
                    <span class="status-badge status-${record.status}">
                        ${record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    enableReportButtons() {
        const courseId = document.getElementById('reportCourse').value;
        const hasValue = courseId && courseId !== '';
        document.querySelectorAll('.report-buttons button').forEach(btn => {
            btn.disabled = !hasValue;
        });
    }

    enableStatsButton() {
        const courseId = document.getElementById('statsCourse').value;
        const hasValue = courseId && courseId !== '';
        document.querySelector('#statistics-tab .btn-block').disabled = !hasValue;
    }

    exportCourseReportCSV() {
        const courseId = document.getElementById('reportCourse').value;
        if (!courseId) {
            this.showError('Please select a course');
            return;
        }

        this.api.exportAttendanceCSV(courseId).then(() => {
            this.showSuccess('CSV exported');
        }).catch(() => {
            this.showError('Failed to export CSV');
        });
    }

    exportCourseReportPDF() {
        const courseId = document.getElementById('reportCourse').value;
        if (!courseId) {
            this.showError('Please select a course');
            return;
        }

        this.api.exportAttendancePDF(courseId).then(() => {
            this.showSuccess('PDF exported');
        }).catch(() => {
            this.showError('Failed to export PDF');
        });
    }

    async viewCourseStatistics() {
        const courseId = document.getElementById('statsCourse').value;
        if (!courseId) {
            this.showError('Please select a course');
            return;
        }

        try {
            const response = await this.api.getLecturerCourseStats(courseId);
            if (response && response.data) {
                this.renderStatistics(response.data);
            }
        } catch (error) {
            console.error('View statistics error:', error);
            this.showError(`Failed to load statistics: ${error.message}`);
        }
    }

    renderStatistics(stats) {
        document.getElementById('totalSessions').textContent = stats.total_sessions || 0;
        document.getElementById('enrolledStudents').textContent = stats.enrolled_students || 0;
        document.getElementById('avgAttendance').textContent = (stats.average_attendance || 0).toFixed(1);
        document.getElementById('lowAttendanceCount').textContent = 
            Math.round((stats.enrolled_students || 0) * (1 - (stats.average_attendance || 0) / 100));

        document.getElementById('statsDisplay').classList.remove('hidden');
    }

    async loadStatistics() {
        try {
            const response = await this.api.getSummaryStatistics();
            if (response && response.data) {
                const stats = response.data;
                
                let totalSessions = 0;
                let totalCheckIns = 0;
                
                // Calculate for lecturer's courses
                for (const course of this.courses) {
                    const sessions = this.sessions.filter(s => s.course_id === course.course_id);
                    totalSessions += sessions.length;
                }

                totalCheckIns = stats.total_attendance_records || 0;

                document.getElementById('totalCourses').textContent = this.courses.length;
                document.getElementById('totalSessionsCreated').textContent = totalSessions;
                document.getElementById('totalCheckIns').textContent = totalCheckIns;
                document.getElementById('systemAverage').textContent = (stats.average_attendance || 0).toFixed(1);

                this.renderCoursePerformanceTable();
            }
        } catch (error) {
            console.error('Load statistics error:', error);
        }
    }

    async renderCoursePerformanceTable() {
        const tbody = document.getElementById('statsTableBody');
        
        if (!this.courses || this.courses.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="6">No courses assigned</td></tr>';
            return;
        }

        const rows = this.courses.map(course => {
            const sessions = this.sessions.filter(s => s.course_id === course.course_id);
            const status = (course.average_attendance || 0) >= 75 ? 'Good' : 'Low';
            const statusClass = status === 'Good' ? 'status-good' : 'status-low';

            return `
                <tr>
                    <td>${course.course_code}</td>
                    <td>${course.course_name}</td>
                    <td>${course.enrolled_students || 0}</td>
                    <td>${sessions.length}</td>
                    <td>${(course.average_attendance || 0).toFixed(1)}%</td>
                    <td><span class="status-badge ${statusClass}">${status}</span></td>
                </tr>
            `;
        }).join('');

        tbody.innerHTML = rows;
    }

    switchTab(e) {
        const tabName = e.currentTarget.dataset.tab;
        
        // Remove active from all menu items
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Remove active from all tab contents
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Add active to clicked menu item
        e.currentTarget.classList.add('active');
        
        // Add active to corresponding tab
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Populate dropdowns when switching to specific tabs
        if (tabName === 'attendance') {
            this.loadAttendanceForCourse();
        }
    }

    showSuccess(message) {
        alert('✓ ' + message);
    }

    showError(message) {
        alert('✗ ' + message);
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('role');
        localStorage.removeItem('user');
        window.location.href = '../pages/login.html';
    }
}

// Initialize dashboard when DOM is ready
let lecturer;
document.addEventListener('DOMContentLoaded', () => {
    lecturer = new LecturerDashboard();
});
