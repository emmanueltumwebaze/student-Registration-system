/**
 * API Communication Layer
 */
class API {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    /**
     * Get authorization header
     */
    getAuthHeader() {
        const token = localStorage.getItem('access_token');
        if (!token) return {};
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeader(),
            ...options.headers
        };

        const config = {
            method: options.method || 'GET',
            headers,
            cache: options.method === 'GET' || !options.method ? 'no-store' : undefined
        };

        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);

            // Handle unauthorized (token expired)
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/pages/login.html';
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                // Backend returns error as 'error' field
                throw new Error(data.error || data.message || `HTTP Error: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async download(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'GET',
            headers: this.getAuthHeader(),
            cache: 'no-store'
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/pages/login.html';
            return;
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Download failed: HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
        const filename = filenameMatch ? filenameMatch[1] : 'attendance-report';
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(downloadUrl);
    }

    // ==================== Authentication ====================
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: userData
        });
    }

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { email, password }
        });
    }

    async getProfile() {
        return this.request('/auth/profile');
    }

    async updateProfile(userData) {
        return this.request('/auth/profile', {
            method: 'PUT',
            body: userData
        });
    }

    // ==================== Departments ====================
    async getDepartments() {
        return this.request('/admin/departments');
    }

    async getDepartment(deptId) {
        return this.request(`/admin/departments/${deptId}`);
    }

    async createDepartment(data) {
        return this.request('/admin/departments', {
            method: 'POST',
            body: data
        });
    }

    async updateDepartment(deptId, data) {
        return this.request(`/admin/departments/${deptId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteDepartment(deptId) {
        return this.request(`/admin/departments/${deptId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Programs ====================
    async getPrograms() {
        return this.request('/admin/programs');
    }

    async getProgram(progId) {
        return this.request(`/admin/programs/${progId}`);
    }

    async createProgram(data) {
        return this.request('/admin/programs', {
            method: 'POST',
            body: data
        });
    }

    async updateProgram(progId, data) {
        return this.request(`/admin/programs/${progId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteProgram(progId) {
        return this.request(`/admin/programs/${progId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Courses ====================
    async getCourses() {
        return this.request('/admin/courses');
    }

    async getCourse(courseId) {
        return this.request(`/admin/courses/${courseId}`);
    }

    async createCourse(data) {
        return this.request('/admin/courses', {
            method: 'POST',
            body: data
        });
    }

    async updateCourse(courseId, data) {
        return this.request(`/admin/courses/${courseId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteCourse(courseId) {
        return this.request(`/admin/courses/${courseId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Students ====================
    async getStudents() {
        return this.request('/admin/students');
    }

    async registerStudent(data) {
        return this.request('/admin/students', {
            method: 'POST',
            body: data
        });
    }

    async getStudent(studentId) {
        return this.request(`/admin/students/${studentId}`);
    }

    async updateStudent(studentId, data) {
        return this.request(`/admin/students/${studentId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteStudent(studentId) {
        return this.request(`/admin/students/${studentId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Lecturers ====================
    async getLecturers() {
        return this.request('/admin/lecturers');
    }

    async registerLecturer(data) {
        return this.request('/admin/lecturers', {
            method: 'POST',
            body: data
        });
    }

    async getLecturer(lecturerId) {
        return this.request(`/admin/lecturers/${lecturerId}`);
    }

    async updateLecturer(lecturerId, data) {
        return this.request(`/admin/lecturers/${lecturerId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteLecturer(lecturerId) {
        return this.request(`/admin/lecturers/${lecturerId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Users ====================
    async getUsers() {
        return this.request('/admin/users');
    }

    async getUser(userId) {
        return this.request(`/admin/users/${userId}`);
    }

    async toggleUserStatus(userId, isActive) {
        return this.request(`/admin/users/${userId}/status`, {
            method: 'PUT',
            body: { is_active: isActive }
        });
    }

    async deleteUser(userId) {
        return this.request(`/admin/users/${userId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Statistics ====================
    async getStatistics() {
        return this.request('/admin/statistics');
    }

    // ==================== Course-Lecturer Assignments ====================
    async getCourseLecturers() {
        return this.request('/assignments/course-lecturers');
    }

    async assignLecturerToCourse(data) {
        return this.request('/assignments/course-lecturers', {
            method: 'POST',
            body: data
        });
    }

    async getCourseLecturer(assignmentId) {
        return this.request(`/assignments/course-lecturers/${assignmentId}`);
    }

    async updateCourseLecturer(assignmentId, data) {
        return this.request(`/assignments/course-lecturers/${assignmentId}`, {
            method: 'PUT',
            body: data
        });
    }

    async removeCourseLecturer(assignmentId) {
        return this.request(`/assignments/course-lecturers/${assignmentId}`, {
            method: 'DELETE'
        });
    }

    async getCourseLecturersAll(courseId) {
        return this.request(`/assignments/course-lecturers/course/${courseId}`);
    }

    // ==================== Student Course Registrations ====================
    async getStudentCourseEnrollments() {
        return this.request('/assignments/student-courses');
    }

    async enrollStudentInCourse(data) {
        return this.request('/assignments/student-courses', {
            method: 'POST',
            body: data
        });
    }

    async getStudentCourse(enrollmentId) {
        return this.request(`/assignments/student-courses/${enrollmentId}`);
    }

    async updateStudentCourse(enrollmentId, data) {
        return this.request(`/assignments/student-courses/${enrollmentId}`, {
            method: 'PUT',
            body: data
        });
    }

    async removeStudentCourse(enrollmentId) {
        return this.request(`/assignments/student-courses/${enrollmentId}`, {
            method: 'DELETE'
        });
    }

    async getStudentEnrolledCourses(studentId) {
        return this.request(`/assignments/student-courses/student/${studentId}`);
    }

    async getCourseEnrolledStudents(courseId) {
        return this.request(`/assignments/student-courses/course/${courseId}`);
    }

    async bulkEnrollStudents(data) {
        return this.request('/assignments/bulk-enroll', {
            method: 'POST',
            body: data
        });
    }

    // ==================== Assignment Summary ====================
    async getLecturerSummary(lecturerId) {
        return this.request(`/assignments/summary/lecturer/${lecturerId}`);
    }

    async getCourseSummary(courseId) {
        return this.request(`/assignments/summary/course/${courseId}`);
    }

    // ==================== Attendance Sessions ====================
    async getSessions() {
        return this.request('/attendance/sessions');
    }

    async createSession(data) {
        return this.request('/attendance/sessions', {
            method: 'POST',
            body: data
        });
    }

    async getSession(sessionId) {
        return this.request(`/attendance/sessions/${sessionId}`);
    }

    async updateSession(sessionId, data) {
        return this.request(`/attendance/sessions/${sessionId}`, {
            method: 'PUT',
            body: data
        });
    }

    async deleteSession(sessionId) {
        return this.request(`/attendance/sessions/${sessionId}`, {
            method: 'DELETE'
        });
    }

    async getCourseSessions(courseId) {
        return this.request(`/attendance/sessions/course/${courseId}`);
    }

    // ==================== Attendance Check-in ====================
    async checkIn(sessionCode) {
        return this.request('/attendance/check-in', {
            method: 'POST',
            body: { session_code: sessionCode }
        });
    }

    async getSessionAttendance(sessionId) {
        return this.request(`/attendance/attendance/${sessionId}`);
    }

    async getStudentAttendance(studentId) {
        return this.request(`/attendance/attendance/student/${studentId}`);
    }

    async getCourseAttendance(courseId) {
        return this.request(`/attendance/attendance/course/${courseId}`);
    }

    // ==================== Attendance Warnings ====================
    async getWarnings() {
        return this.request('/attendance/warnings');
    }

    async getStudentWarnings(studentId) {
        return this.request(`/attendance/warnings/student/${studentId}`);
    }

    async acknowledgeWarning(warningId) {
        return this.request(`/attendance/warnings/acknowledge/${warningId}`, {
            method: 'PUT'
        });
    }

    async generateWarnings(threshold = 75, criticalThreshold = 50) {
        return this.request('/attendance/warnings/generate', {
            method: 'POST',
            body: {
                threshold: threshold,
                critical_threshold: criticalThreshold
            }
        });
    }

    // ==================== QR Code ====================
    async downloadQRCode(sessionId) {
        return this.request(`/attendance/qr/${sessionId}`);
    }

    // ==================== Attendance Statistics ====================
    async getCourseAttendanceStats(courseId) {
        return this.request(`/attendance/statistics/course/${courseId}`);
    }

    async getStudentAttendanceStats(studentId) {
        return this.request(`/attendance/statistics/student/${studentId}`);
    }

    // ==================== Reporting & Analytics ====================
    
    // Attendance Reports
    async getCourseAttendanceReport(courseId, startDate = null, endDate = null) {
        let url = `/reports/attendance/course/${courseId}`;
        if (startDate) url += `?start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        return this.request(url);
    }

    async getStudentAttendanceReport(studentId) {
        return this.request(`/reports/attendance/student/${studentId}`);
    }

    async getDepartmentAttendanceReport(deptId) {
        return this.request(`/reports/attendance/department/${deptId}`);
    }

    // Statistics
    async getSummaryStatistics() {
        return this.request('/reports/statistics/summary');
    }

    async getStatisticsByCourse() {
        return this.request('/reports/statistics/by-course');
    }

    async getStatisticsByStudent() {
        return this.request('/reports/statistics/by-student');
    }

    async getStatisticsByDateRange(startDate, endDate) {
        return this.request(`/reports/statistics/by-date-range?start_date=${startDate}&end_date=${endDate}`);
    }

    // Low Attendance Tracking
    async getLowAttendanceStudents(threshold = 75) {
        return this.request(`/reports/low-attendance/students?threshold=${threshold}`);
    }

    async getLowAttendanceCourses(threshold = 75) {
        return this.request(`/reports/low-attendance/courses?threshold=${threshold}`);
    }

    async getLowAttendanceWarnings() {
        return this.request('/reports/low-attendance/warnings');
    }

    // Report Export
    async exportAttendanceCSV(courseId) {
        return this.download(`/reports/export/attendance-csv/${courseId}`);
    }

    async exportAttendancePDF(courseId) {
        return this.download(`/reports/export/attendance-pdf/${courseId}`);
    }

    // ==================== Student Profile & Data ====================
    async getUserProfile() {
        return this.request('/auth/profile');
    }

    // Student Courses
    async getStudentCourses() {
        return this.request('/student/courses');
    }

    // Student Attendance
    async getStudentAttendance() {
        return this.request('/student/attendance');
    }

    // Student Warnings  
    async getStudentWarnings() {
        return this.request('/student/warnings');
    }

    async acknowledgeWarningStudent(warningId) {
        return this.request(`/student/warnings/${warningId}/acknowledge`, {
            method: 'PUT'
        });
    }

    // Student Statistics
    async getStudentStats() {
        return this.request('/student/statistics');
    }

    // ==================== Lecturer Data ====================

    // Lecturer Courses
    async getLecturerCourses() {
        return this.request('/lecturer/courses');
    }

    // Lecturer Sessions
    async getLecturerSessions() {
        return this.request('/lecturer/sessions');
    }

    // Lecturer Course Statistics
    async getLecturerCourseStats(courseId) {
        return this.request(`/lecturer/courses/${courseId}/statistics`);
    }

    // ==================== Admin Helpers ====================
    
    // Helper to get all courses (alias)
    async getAllCourses() {
        return this.getCourses();
    }

    // Helper to get all students (alias)
    async getAllStudents() {
        return this.getStudents();
    }

    // Helper to get all departments (alias)
    async getAllDepartments() {
        return this.getDepartments();
    }
}

// Initialize API instance
const api = new API(CONFIG.API_BASE_URL);
