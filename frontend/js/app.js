/**
 * Main Application Entry Point
 */
/*function logout(){
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/pages/login.html';
}*/
// Utility functions
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page=> page.classList.remove('active'));
    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add('active');
    }
}

function showAlert(message, type = 'info') {
    const alertHTML = `
        <div class="alert alert-${type}">
            <span>${message}</span>
        </div>
    `;
    const container = document.querySelector('main') || document.body;
    const alertEl = document.createElement('div');
    alertEl.innerHTML = alertHTML;
    container.insertBefore(alertEl.firstElementChild, container.firstChild);

    setTimeout(() => {
        alertEl.firstElementChild?.remove();
    }, 5000);
}

function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = new URL('../pages/login.html', window.location.href).href;
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const isLoginPage = path.includes('/login');
    const isLogoutPage = path.includes('/logout');

    if (!isAuthenticated() && !isLoginPage && !isLogoutPage) {
        window.location.href = '/pages/login.html';
        return;
    }

    if (isAuthenticated() && isLoginPage) {
        const user = getUser();
        const dashboards = {
            admin: '/pages/admin-dashboard.html',
            lecturer: '/pages/lecturer-dashboard.html',
            student: '/pages/student-dashboard.html'
        };
        window.location.href = dashboards[user?.role] || '/pages/login.html';
        return;
    }

    // Setup logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Display user info
    const user = getUser();
    if (user) {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            userNameEl.textContent = `${user.first_name} ${user.last_name}`;
        }

        const userRoleEl = document.getElementById('user-role');
        if (userRoleEl) {
            userRoleEl.textContent = user.role.toUpperCase();
        }
    }
});

/**
 * Pages Module - Single Page Application
 */
const Pages = {
    home: () => {
        showPage('home-page');
    },

    login: () => {
        showPage('login-page');
    },

    dashboard: () => {
        const user = getUser();
        if (!user) {
            window.location.href = '/pages/login.html';
            return;
        }

        switch (user.role) {
            case 'admin':
                Pages.adminDashboard();
                break;
            case 'lecturer':
                Pages.lecturerDashboard();
                break;
            case 'student':
                Pages.studentDashboard();
                break;
            default:
                window.location.href = '/pages/login.html';
        }
    },

    adminDashboard: () => {
        showPage('admin-dashboard');
    },

    lecturerDashboard: () => {
        showPage('lecturer-dashboard');
    },

    studentDashboard: () => {
        showPage('student-dashboard');
    }
};

// Export for use
if (typeof window !== 'undefined') {
    window.Pages = Pages;
    window.showAlert = showAlert;
    window.showPage = showPage;
    window.logout = logout;
}
