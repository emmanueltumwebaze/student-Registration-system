/**
 * Student Dashboard Manager
 * Handles student course viewing, attendance history, warnings, and check-in
 */

class StudentDashboard {
    constructor() {
        this.api = api;  // Use global API instance
        this.studentId = null;
        this.currentUser = null;
        this.courses = [];
        this.attendanceRecords = [];
        this.warnings = [];
        
        this.init();
    }

    async init() {
        // Check authentication
        const token = localStorage.getItem('access_token');
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const role = (user.role || '').toLowerCase();
        
        if (!token || role !== 'student') {
            window.location.href = new URL('../pages/login.html', window.location.href).href;
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
            window.location.href = new URL('../pages/login.html', window.location.href).href;
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

        // Course filter
        document.getElementById('courseFilterSelect').addEventListener('change', (e) => {
            this.filterAttendanceByCourse(e.target.value);
        });

        // Check-in button
        document.getElementById('checkInBtn').addEventListener('click', () => this.submitCheckIn());

        // Session code input - allow enter key
        document.getElementById('sessionCode').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.submitCheckIn();
            }
        });

        // Modal close button
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal on background click
        document.getElementById('courseDetailModal').addEventListener('click', (e) => {
            if (e.target.id === 'courseDetailModal') {
                this.closeModal();
            }
        });
    }

    async loadData() {
        try {
            // Load courses
            await this.loadCourses();
            
            // Load attendance
            await this.loadAttendance();
            
            // Load warnings
            await this.loadWarnings();
            
            // Load statistics
            await this.loadStatistics();
        } catch (error) {
            console.error('Load data error:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadCourses() {
        try {
            const response = await this.api.getStudentCourses();
            if (response) {
                this.courses = response.data || [];
                this.renderCourses();
                this.populateCourseFilter();
            }
        } catch (error) {
            console.error('Load courses error:', error);
        }
    }

    renderCourses() {
        const coursesGrid = document.getElementById('coursesGrid');
        
        if (!this.courses || this.courses.length === 0) {
            coursesGrid.innerHTML = '<div class="empty-state">No courses enrolled</div>';
            return;
        }

        coursesGrid.innerHTML = this.courses.map(course => `
            <div class="course-card" onclick="dashboard.showCourseDetail(${course.course_id})">
                <div class="course-code">${course.course_code}</div>
                <div class="course-name">${course.course_name}</div>
                <div class="course-lecturer">👨‍🏫 ${course.lecturer_name || 'TBA'}</div>
                
                <div class="course-attendance">
                    <div>
                        <div class="attendance-percentage">${course.attendance_percentage?.toFixed(1) || 0}%</div>
                        <div class="attendance-label">Attendance</div>
                    </div>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${course.attendance_percentage?.toFixed(1) || 0}%"></div>
                </div>
                
                <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                    ${this.getAttendanceStatus(course.attendance_percentage)}
                </div>
            </div>
        `).join('');
    }

    getAttendanceStatus(percentage) {
        if (percentage === undefined || percentage === null) return '🔄 No records';
        if (percentage >= 75) return '✅ Good Standing';
        if (percentage >= 50) return '⚠️ Low Attendance';
        return '🚨 Critical';
    }

    showCourseDetail(courseId) {
        const course = this.courses.find(c => c.course_id === courseId);
        if (!course) return;

        const contentDiv = document.getElementById('courseDetailContent');
        const titleDiv = document.getElementById('courseDetailTitle');
        
        titleDiv.textContent = `${course.course_code} - ${course.course_name}`;
        
        contentDiv.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Course Code</div>
                <div class="detail-value">${course.course_code}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Course Name</div>
                <div class="detail-value">${course.course_name}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Lecturer</div>
                <div class="detail-value">${course.lecturer_name || 'TBA'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Enrollment Date</div>
                <div class="detail-value">${new Date(course.enrolled_at).toLocaleDateString()}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Attendance</div>
                <div class="detail-value">
                    ${course.attendance_percentage?.toFixed(2) || 0}%
                    <span class="status-badge status-${this.getStatusClass(course.attendance_percentage)}">
                        ${this.getAttendanceStatusText(course.attendance_percentage)}
                    </span>
                </div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Status</div>
                <div class="detail-value">${course.is_active ? '✅ Active' : '❌ Inactive'}</div>
            </div>
        `;

        document.getElementById('courseDetailModal').classList.add('active');
    }

    closeModal() {
        document.getElementById('courseDetailModal').classList.remove('active');
    }

    getStatusClass(percentage) {
        if (percentage >= 75) return 'good';
        if (percentage >= 50) return 'low';
        return 'critical';
    }

    getAttendanceStatusText(percentage) {
        if (percentage >= 75) return 'Good';
        if (percentage >= 50) return 'Low';
        return 'Critical';
    }

    populateCourseFilter() {
        const select = document.getElementById('courseFilterSelect');
        select.innerHTML = '<option value="">Select a course...</option>' +
            this.courses.map(course => `
                <option value="${course.course_id}">${course.course_code} - ${course.course_name}</option>
            `).join('');
    }

    async loadAttendance() {
        try {
            const response = await this.api.getStudentAttendance();
            if (response) {
                this.attendanceRecords = response.data || [];
                this.renderAttendance();
            }
        } catch (error) {
            console.error('Load attendance error:', error);
        }
    }

    renderAttendance() {
        const tbody = document.getElementById('attendanceTableBody');
        
        if (!this.attendanceRecords || this.attendanceRecords.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="4">No attendance records found</td></tr>';
            return;
        }

        tbody.innerHTML = this.attendanceRecords.map(record => `
            <tr>
                <td>${new Date(record.session_date).toLocaleDateString()}</td>
                <td>${record.course_code}</td>
                <td>${new Date(record.check_in_time).toLocaleTimeString()}</td>
                <td>
                    <span class="status-badge status-${record.status}">
                        ${record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    filterAttendanceByCourse(courseId) {
        const tbody = document.getElementById('attendanceTableBody');
        
        let filtered = this.attendanceRecords;
        if (courseId) {
            filtered = this.attendanceRecords.filter(r => r.course_id === parseInt(courseId));
        }

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="4">No attendance records found for selected course</td></tr>';
            return;
        }

        tbody.innerHTML = filtered.map(record => `
            <tr>
                <td>${new Date(record.session_date).toLocaleDateString()}</td>
                <td>${record.course_code}</td>
                <td>${new Date(record.check_in_time).toLocaleTimeString()}</td>
                <td>
                    <span class="status-badge status-${record.status}">
                        ${record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    async loadWarnings() {
        try {
            const response = await this.api.getStudentWarnings();
            if (response) {
                this.warnings = response.data || [];
                this.renderWarnings();
            }
        } catch (error) {
            console.error('Load warnings error:', error);
        }
    }

    renderWarnings() {
        const container = document.getElementById('warningsContainer');
        
        if (!this.warnings || this.warnings.length === 0) {
            container.innerHTML = '<div class="empty-state">✓ No warnings. Great attendance!</div>';
            return;
        }

        container.innerHTML = this.warnings.map(warning => `
            <div class="warning-card ${warning.warning_level === 'critical' ? 'critical' : ''}">
                <div class="warning-header">
                    <div class="warning-title">${warning.course_code} - ${warning.course_name}</div>
                    <div class="warning-level warning-level-${warning.warning_level}">
                        ${warning.warning_level}
                    </div>
                </div>
                
                <div class="warning-details">
                    <div class="warning-detail-item">
                        <div class="warning-detail-label">Attendance Percentage</div>
                        <div class="warning-detail-value">${warning.attendance_percentage?.toFixed(2) || 0}%</div>
                    </div>
                    <div class="warning-detail-item">
                        <div class="warning-detail-label">Created Date</div>
                        <div class="warning-detail-value">${new Date(warning.created_at).toLocaleDateString()}</div>
                    </div>
                    <div class="warning-detail-item">
                        <div class="warning-detail-label">Status</div>
                        <div class="warning-detail-value">${warning.is_acknowledged ? '✓ Acknowledged' : 'Pending'}</div>
                    </div>
                </div>
                
                <div class="warning-actions">
                    ${!warning.is_acknowledged ? `
                        <button class="warning-action-btn" onclick="dashboard.acknowledgeWarning(${warning.id})">
                            Acknowledge
                        </button>
                    ` : '<span style="color: #6c757d; font-size: 0.9rem;">✓ Acknowledged</span>'}
                </div>
            </div>
        `).join('');
    }

    async acknowledgeWarning(warningId) {
        try {
            const response = await this.api.acknowledgeWarningStudent(warningId);
            if (response) {
                this.showSuccess('Warning acknowledged');
                await this.loadWarnings();
            } else {
                this.showError('Failed to acknowledge warning');
            }
        } catch (error) {
            console.error('Acknowledge warning error:', error);
            this.showError('Error acknowledging warning');
        }
    }

    async loadStatistics() {
        try {
            const response = await this.api.getStudentStats();
            if (response) {
                this.renderStatistics(response.data || {});
            }
        } catch (error) {
            console.error('Load statistics error:', error);
        }
    }

    renderStatistics(stats) {
        // Update stat cards
        document.getElementById('overallAverage').textContent = 
            (stats.overall_average || 0).toFixed(1) + '%';
        
        document.getElementById('enrolledCourses').textContent = 
            stats.courses ? stats.courses.length : 0;
        
        const goodCourses = (stats.courses || []).filter(c => c.attendance_percentage >= 75).length;
        document.getElementById('goodCourses').textContent = goodCourses;
        
        const atRiskCourses = (stats.courses || []).filter(c => c.attendance_percentage < 75).length;
        document.getElementById('atRiskCourses').textContent = atRiskCourses;
        
        // Render statistics table
        const tbody = document.getElementById('statisticsTableBody');
        if (!stats.courses || stats.courses.length === 0) {
            tbody.innerHTML = '<tr class="empty-state"><td colspan="4">No courses enrolled</td></tr>';
            return;
        }

        tbody.innerHTML = stats.courses.map(course => `
            <tr>
                <td>${course.course_code}</td>
                <td>${course.course_name}</td>
                <td>${course.attendance_percentage?.toFixed(2) || 0}%</td>
                <td>
                    <span class="status-badge status-${this.getStatusClass(course.attendance_percentage)}">
                        ${this.getAttendanceStatusText(course.attendance_percentage)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    async submitCheckIn() {
        const sessionCode = document.getElementById('sessionCode').value.trim();
        
        if (!sessionCode) {
            this.showCheckInError('Please enter a session code');
            return;
        }

        try {
            const response = await this.api.checkIn(sessionCode);
            if (response && response.data) {
                this.showCheckInSuccess(`Check-in successful: ${response.data.status}`);
                document.getElementById('sessionCode').value = '';
                await this.loadAttendance();
                this.loadRecentCheckIns();
            } else {
                this.showCheckInError(response.message || 'Check-in failed');
            }
        } catch (error) {
            console.error('Check-in error:', error);
            // Show the actual error message from backend
            this.showCheckInError(error.message || 'Error during check-in');
        }
    }

    loadRecentCheckIns() {
        const recentList = document.getElementById('recentCheckInsList');
        
        if (!this.attendanceRecords || this.attendanceRecords.length === 0) {
            recentList.innerHTML = '<div class="empty-state">No check-ins yet</div>';
            return;
        }

        // Get last 5 check-ins
        const recent = this.attendanceRecords.slice(-5).reverse();
        
        recentList.innerHTML = recent.map(record => `
            <div class="check-in-item">
                <div class="check-in-item-course">${record.course_code}</div>
                <div class="check-in-item-time">${new Date(record.check_in_time).toLocaleTimeString()}</div>
                <div class="status-badge status-${record.status}">${record.status}</div>
            </div>
        `).join('');
    }

    showCheckInSuccess(message) {
        const messageBox = document.getElementById('checkInMessage');
        messageBox.textContent = message;
        messageBox.className = 'message-box success';
        setTimeout(() => messageBox.classList.add('hidden'), 3000);
    }

    showCheckInError(message) {
        const messageBox = document.getElementById('checkInMessage');
        messageBox.textContent = message;
        messageBox.className = 'message-box error';
        setTimeout(() => messageBox.classList.add('hidden'), 3000);
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
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new StudentDashboard();
});
