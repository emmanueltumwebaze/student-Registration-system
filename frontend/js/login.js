/**
 * Login Page Logic
 */

class LoginManager {
    constructor() {
        this.form = document.getElementById('login-form');
        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.rememberCheckbox = document.getElementById('remember-me');
        this.alertContainer = document.getElementById('alert-container');
        this.loadingOverlay = document.getElementById('loading-overlay');

        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleLogin(e));
        this.loadRememberedEmail();
    }

    /**
     * Handle login form submission
     */
    async handleLogin(e) {
        e.preventDefault();

        const email = this.emailInput.value.trim();
        const password = this.passwordInput.value;

        // Validation
        if (!email || !password) {
            this.showAlert('Please enter email and password', 'danger');
            return;
        }

        this.showLoading(true);

        try {
            const response = await api.login(email, password);

            if (!response) {
                throw new Error('The server returned an empty login response. Please try again.');
            }

            // The backend returns the login payload inside its data property.
            const responseData = response.data || response;
            if (!responseData.access_token || !responseData.user) {
                throw new Error('The server returned an invalid login response.');
            }

            // Save tokens securely using the cleaned data object variables
            localStorage.setItem('access_token', responseData.access_token);
            localStorage.setItem('refresh_token', responseData.refresh_token || '');
            localStorage.setItem('user', JSON.stringify(responseData.user || { role: 'admin' }));

            // Remember email if checkbox is checked
            if (this.rememberCheckbox.checked) {
                localStorage.setItem('remembered_email', email);
            } else {
                localStorage.removeItem('remembered_email');
            }

            this.showAlert('Login successful! Redirecting...', 'success');

            // Redirect based on role strings
            setTimeout(() => {
                const userRole = responseData.user ? responseData.user.role : 'admin';
                this.redirectToDashboard(userRole);
            }, 1000);

        } catch (error) {
            this.showLoading(false);
            // Show the actual error message from backend
            const message = error.message || 'Login failed. Please try again.';
            this.showAlert(message, 'danger');
        }
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.add('active');
            this.form.style.opacity = '0.5';
            this.form.style.pointerEvents = 'none';
        } else {
            this.loadingOverlay.classList.remove('active');
            this.form.style.opacity = '1';
            this.form.style.pointerEvents = 'auto';
        }
    }

    /**
     * Display alert message
     */
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `<span>${message}</span>`;
        this.alertContainer.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    /**
     * Load remembered email
     */
    loadRememberedEmail() {
        const rememberedEmail = localStorage.getItem('remembered_email');
        if (rememberedEmail) {
            this.emailInput.value = rememberedEmail;
            this.rememberCheckbox.checked = true;
        }
    }

    /**
     * Redirect to appropriate dashboard
     */
    redirectToDashboard(role) {
        const dashboards = {
            'admin': 'admin-dashboard.html',
            'lecturer': 'lecturer-dashboard.html',
            'student': 'student-dashboard.html'
        };

        const dashboard = dashboards[role] || 'admin-dashboard.html';
        window.location.href = dashboard;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in
    if (localStorage.getItem('access_token')) {
        const user = JSON.parse(localStorage.getItem('user'));
        if (user) {
            // Show option to redirect or logout
            const redirectTimer = setTimeout(() => {
                // Auto redirect after 2 seconds if still logged in
                const dashboards = {
                    'admin': 'admin-dashboard.html',
                    'lecturer': 'lecturer-dashboard.html',
                    'student': 'student-dashboard.html'
                };
                window.location.href = dashboards[user.role] || 'admin-dashboard.html';
            }, 2000);

            // Provide logout option
            const logoutLink = document.createElement('div');
            logoutLink.style.cssText = 'text-align: center; padding: 20px; background: #f0f0f0; margin-top: 20px; border-radius: 5px;';
            logoutLink.innerHTML = `
                <p>You are already logged in as <strong>${user.first_name} ${user.last_name}</strong></p>
                <p>Redirecting to dashboard in 2 seconds...</p>
                <button id="logout-from-login" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px;">Logout & Use Different Account</button>
            `;
            
            const formContainer = document.querySelector('.login-form');
            if (formContainer) {
                formContainer.parentNode.insertBefore(logoutLink, formContainer.nextSibling);
            }

            document.getElementById('logout-from-login').addEventListener('click', () => {
                clearTimeout(redirectTimer);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                location.reload();
            });
            
            return;
        }
    }

    new LoginManager();
});
