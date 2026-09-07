/**
 * Configuration
 */
const CONFIG = {
    API_BASE_URL: 'https://student-registration-system-tdtk.onrender.com/api',
    APP_NAME: 'Student-Attendance-System',
    // Token expiration in milliseconds (24 hours)
    TOKEN_EXPIRATION: 24 * 60 * 60 * 1000,
    // Refresh token expiration (30 days)
    REFRESH_TOKEN_EXPIRATION: 30 * 24 * 60 * 60 * 1000,
    // Low attendance threshold (percentage)
    LOW_ATTENDANCE_THRESHOLD: 75,
    // Critical attendance threshold
    CRITICAL_ATTENDANCE_THRESHOLD: 50
};

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
