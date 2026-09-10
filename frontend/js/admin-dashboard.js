/**
 * Admin Dashboard Logic
 */

class AdminDashboard {
    constructor() {
        AdminDashboard.instance = this;
        this.currentTab = 'dashboard';
        this.currentEditId = null;
        this.currentEditType = null;
        this.modal = document.getElementById('modal');
        this.checkAuth();
        this.init();
    }

    checkAuth() {
        // Check if authenticated and is admin
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        
        if (!token || !userStr) {
            window.location.href = new URL('../pages/login.html', window.location.href).href;
            return;
        }

        const user = JSON.parse(userStr);
        if (user.role !== 'admin') {
            window.location.href = new URL('../pages/login.html', window.location.href).href;
            return;
        }
    }

    init() {
        // Load dashboard data
        this.loadStatistics();
        this.loadDepartments();
        this.loadPrograms();
        this.loadCourses();
        this.loadStudents();
        this.loadLecturers();
        this.loadAssignments();
        this.loadEnrollments();
        this.loadUsers();
        AdminDashboard.populateSelects();
        AdminDashboard.populateReportSelects();
        AdminDashboard.loadAnalytics();

        // Set user name
        const user = JSON.parse(localStorage.getItem('user'));
        document.getElementById('user-name').textContent = `${user.first_name} ${user.last_name}`;

        // Set initial tab
        this.selectTab('dashboard');
    }

    /**
     * Load statistics
     */
    async loadStatistics() {
        try {
            const response = await api.getStatistics();
            const stats = response.data;
            document.getElementById('total-users').textContent = stats.total_users;
            document.getElementById('total-students').textContent = stats.total_students;
            document.getElementById('total-lecturers').textContent = stats.total_lecturers;
            document.getElementById('total-departments').textContent = stats.total_departments;
            document.getElementById('total-programs').textContent = stats.total_programs;
            document.getElementById('total-courses').textContent = stats.total_courses;
        } catch (error) {
            this.showAlert(`Failed to load statistics: ${error.message}`, 'danger');
        }
    }

    /**
     * Load departments
     */
    async loadDepartments(silent = false) {
        try {
            const response = await api.getDepartments();
            const tbody = document.querySelector('#departments-table tbody');
            tbody.innerHTML = '';

            (response.data || []).forEach(dept => {
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${dept.code}</strong></td>
                        <td>${dept.name}</td>
                        <td>${dept.description || '-'}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.editDepartment(${dept.id})">Edit</button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteDepartment(${dept.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            console.error('Failed to load departments:', error);
        }
    }

    /**
     * Load programs
     */
    async loadPrograms(silent = false) {
        try {
            const response = await api.getPrograms();
            const tbody = document.querySelector('#programs-table tbody');
            tbody.innerHTML = '';

            response.data.forEach(prog => {
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${prog.code}</strong></td>
                        <td>${prog.name}</td>
                        <td>${prog.department_id}</td>
                        <td>${prog.duration_years}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.editProgram(${prog.id})">Edit</button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteProgram(${prog.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            this.showAlert(`Failed to load programs: ${error.message}`, 'danger');
        }
    }

    /**
     * Load courses
     */
    async loadCourses() {
        try {
            const response = await api.getCourses();
            const tbody = document.querySelector('#courses-table tbody');
            tbody.innerHTML = '';

            response.data.forEach(course => {
                const status = course.is_active ? 
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';
                
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${course.code}</strong></td>
                        <td>${course.name}</td>
                        <td>${course.program_id}</td>
                        <td>${course.credits}</td>
                        <td>${status}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.editCourse(${course.id})">Edit</button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteCourse(${course.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            this.showAlert(`Failed to load courses: ${error.message}`, 'danger');
        }
    }

    /**
     * Load students
     */
    async loadStudents(silent = false) {
        try {
            const response = await api.getStudents();
            const tbody = document.querySelector('#students-table tbody');
            tbody.innerHTML = '';

            (response.data || []).forEach(student => {
                const status = student.is_active ?
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';
                const studentUser = student.user || {};

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${student.student_id}</strong></td>
                        <td>${studentUser.first_name || ''} ${studentUser.last_name || ''}</td>
                        <td>${studentUser.email || '-'}</td>
                        <td>${student.program_id}</td>
                        <td>${status}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.editStudent(${student.id})">Edit</button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteStudent(${student.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            console.error('Failed to load students:', error);
        }
    }

    /**
     * Load lecturers
     */
    async loadLecturers(silent = false) {
        try {
            const response = await api.getLecturers();
            const tbody = document.querySelector('#lecturers-table tbody');
            tbody.innerHTML = '';

            response.data.forEach(lecturer => {
                const status = lecturer.is_active ?
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${lecturer.lecturer_id}</strong></td>
                        <td>${lecturer.user.first_name} ${lecturer.user.last_name}</td>
                        <td>${lecturer.user.email}</td>
                        <td>${lecturer.department_id}</td>
                        <td>${lecturer.specialization || '-'}</td>
                        <td>${status}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.editLecturer(${lecturer.id})">Edit</button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteLecturer(${lecturer.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            this.showAlert(`Failed to load lecturers: ${error.message}`, 'danger');
        }
    }

    /**
     * Load assignments
     */
    async loadAssignments(silent = false) {
        try {
            const response = await api.getCourseLecturers();
            const tbody = document.querySelector('#assignments-table tbody');
            tbody.innerHTML = '';

            (response.data || []).forEach(assign => {
                const status = assign.is_active ?
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';

                const assigned = new Date(assign.assigned_date).toLocaleDateString();

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${assign.course_code}</strong></td>
                        <td>${assign.course_name}</td>
                        <td>${assign.lecturer_name}</td>
                        <td>${assigned}</td>
                        <td>${status}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.removeAssignment(${assign.id})">Remove</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            console.error('Failed to load assignments:', error);
        }
    }

    /**
     * Load enrollments
     */
    async loadEnrollments(silent = false) {
        try {
            const response = await api.getStudentCourseEnrollments();
            const tbody = document.querySelector('#enrollments-table tbody');
            tbody.innerHTML = '';

            (response.data || []).forEach(enrollment => {
                const status = enrollment.is_active ?
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';

                const enrolled = new Date(enrollment.enrollment_date).toLocaleDateString();

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${enrollment.student_id_num}</strong></td>
                        <td>${enrollment.student_name}</td>
                        <td><strong>${enrollment.course_code}</strong></td>
                        <td>${enrollment.course_name}</td>
                        <td>${enrolled}</td>
                        <td>${status}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.removeEnrollment(${enrollment.id})">Remove</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            if (silent) throw error;
            console.error('Failed to load enrollments:', error);
        }
    }

    /**
     * Load users
     */
    async loadUsers() {
        try {
            const response = await api.getUsers();
            const tbody = document.querySelector('#users-table tbody');
            tbody.innerHTML = '';

            response.data.forEach(user => {
                const status = user.is_active ?
                    '<span class="status-badge status-active">Active</span>' :
                    '<span class="status-badge status-inactive">Inactive</span>';

                const created = new Date(user.created_at).toLocaleDateString();

                tbody.innerHTML += `
                    <tr>
                        <td>${user.email}</td>
                        <td>${user.first_name} ${user.last_name}</td>
                        <td><strong>${user.role.toUpperCase()}</strong></td>
                        <td>${status}</td>
                        <td>${created}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="AdminDashboard.toggleUserStatus(${user.id}, ${!user.is_active})">
                                    ${user.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                                <button class="btn-icon btn-delete" onclick="AdminDashboard.deleteUser(${user.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            this.showAlert(`Failed to load users: ${error.message}`, 'danger');
        }
    }

    /**
     * Select tab
     */
    static selectTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected tab
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    /**
     * Show alert
     */
    static showAlert(message, type = 'info') {
        const container = document.getElementById('alert-container');
        if (!container) return;
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.setAttribute('role', 'alert');
        alert.innerHTML = `<span>${message}</span>`;
        container.prepend(alert);
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        setTimeout(() => alert.remove(), 5000);
    }

    /**
     * Open modal
     */
    static async openModal(type) {
        const dashboard = this;
        const form = document.getElementById('modal-form');
        const title = document.getElementById('modal-title');
        
        form.innerHTML = '';
        this.currentEditType = type;
        this.currentEditId = null;

        switch (type) {
            case 'department':
                title.textContent = 'Add Department';
                form.innerHTML = `
                    <div class="form-group">
                        <label>Department Name *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label>Department Code *</label>
                        <input type="text" id="code" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="description"></textarea>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Department</button>
                    </div>
                `;
                form.onsubmit = (e) => this.submitDepartment(e);
                break;

            case 'program':
                title.textContent = 'Add Program';
                form.innerHTML = `
                    <div class="form-group">
                        <label>Program Name *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label>Program Code *</label>
                        <input type="text" id="code" required>
                    </div>
                    <div class="form-group">
                        <label>Department *</label>
                        <select id="department_id" required>
                            <option value="">Select Department</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Duration (Years)</label>
                        <input type="number" id="duration_years" value="4" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="description"></textarea>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Program</button>
                    </div>
                `;
                await this.populateSelects();
                form.onsubmit = (e) => this.submitProgram(e);
                break;

            case 'course':
                title.textContent = 'Add Course';
                form.innerHTML = `
                    <div class="form-group">
                        <label>Course Code *</label>
                        <input type="text" id="code" required>
                    </div>
                    <div class="form-group">
                        <label>Course Name *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label>Program *</label>
                        <select id="program_id" required>
                            <option value="">Select Program</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Credits</label>
                        <input type="number" id="credits" value="3" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="description"></textarea>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Course</button>
                    </div>
                `;
                await this.populateSelects();
                form.onsubmit = (e) => this.submitCourse(e);
                break;
            
            case 'student':
                title.textContent = 'Register Student';
                form.innerHTML = `
                    <div class="form-row">
                        <div class="form-group">
                            <label>First Name *</label>
                            <input type="text" id="first_name" required>
                        </div>
                        <div class="form-group">
                            <label>Last Name *</label>
                            <input type="text" id="last_name" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Email *</label>
                            <input type="email" id="email" required>
                        </div>
                        <div class="form-group">
                            <label>Username *</label>
                            <input type="text" id="username" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Temporary Password *</label>
                            <input type="password" id="password" minlength="6" required>
                        </div>
                        <div class="form-group">
                            <label>Student ID *</label>
                            <input type="text" id="student_id" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Program *</label>
                            <select id="program_id" required>
                                <option value="">Select Program</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Department *</label>
                            <select id="department_id" required>
                                <option value="">Select Department</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Register Student</button>
                    </div>
                `;
                await this.populateSelects();
                form.onsubmit = (e) => this.submitStudent(e);
                break;

            case 'lecturer':
                title.textContent = 'Register Lecturer';
                form.innerHTML = `
                    <div class="form-row">
                        <div class="form-group">
                            <label>First Name *</label>
                            <input type="text" id="first_name" required>
                        </div>
                        <div class="form-group">
                            <label>Last Name *</label>
                            <input type="text" id="last_name" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Email *</label>
                            <input type="email" id="email" required>
                        </div>
                        <div class="form-group">
                            <label>Username *</label>
                            <input type="text" id="username" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Temporary Password *</label>
                            <input type="password" id="password" minlength="6" required>
                        </div>
                        <div class="form-group">
                            <label>Lecturer ID *</label>
                            <input type="text" id="lecturer_id" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group full">
                            <label>Specialization</label>
                            <input type="text" id="specialization">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Department *</label>
                            <select id="department_id" required>
                                <option value="">Select Department</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Register Lecturer</button>
                    </div>
                `;
                await this.populateSelects();
                form.onsubmit = (e) => AdminDashboard.submitLecturer(e);
                break;

            case 'assignment':
                title.textContent = 'Assign Lecturer to Course';
                form.innerHTML = `
                    <div class="form-group">
                        <label>Course *</label>
                        <select id="course_id" required><option value="">Select Course</option></select>
                    </div>
                    <div class="form-group">
                        <label>Lecturer *</label>
                        <select id="lecturer_id" required><option value="">Select Lecturer</option></select>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Assign</button>
                    </div>
                `;
                this.populateAssignmentSelects();
                form.onsubmit = (e) => this.submitAssignment(e);
                break;

            case 'enrollment':
                title.textContent = 'Enroll Student in Course';
                form.innerHTML = `
                    <div class="form-group">
                        <label>Student *</label>
                        <select id="student_id" required><option value="">Select Student</option></select>
                    </div>
                    <div class="form-group">
                        <label>Course *</label>
                        <select id="course_id" required><option value="">Select Course</option></select>
                    </div>
                    <div class="form-buttons">
                        <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                        <button type="submit" class="btn btn-primary">Enroll</button>
                    </div>
                `;
                this.populateEnrollmentSelects();
                form.onsubmit = (e) => this.submitEnrollment(e);
                break;

            // Add more modal types as needed
        }

        const modalE1 = document.getElementById('modal') || document.getElementById('adminModal') || document.getElementById('crudModal');
        if (modalE1){
            modalE1.style.display = 'block';
            modalE1.classList.add('active');
            modalE1.classList.add('show');
        }
    }

    /**
     * Close modal
     */
    static closeModal(){
        const modalE1 = document.getElementById('modal') || document.getElementById('adminModal') || document.getElementById('crudModal');
        if (modalE1){
            modalE1.style.display = 'none';
            modalE1.classList.remove('active');
            modalE1.classList.remove('show');
        }
    }
    /**
     * Populate select dropdowns
     */
    static async populateSelects() {
        try {
            const depts = await api.getDepartments();
            const progs = await api.getPrograms();

            const deptSelect = document.getElementById('department_id');
            if (deptSelect) {
                depts.data.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    deptSelect.appendChild(option);
                });
            }

            const progSelect = document.getElementById('program_id');
            if (progSelect) {
                progs.data.forEach(prog => {
                    const option = document.createElement('option');
                    option.value = prog.id;
                    option.textContent = prog.name;
                    progSelect.appendChild(option);
                });
            }
        } catch (error) {
            this.showAlert(`Failed to load dropdown data: ${error.message}`, 'danger');
        }
    }

    /**
     * Submit department form
     */
    static async submitDepartment(e) {
        e.preventDefault();
        const form = e.currentTarget;
        if (form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        const data = {
            name: document.getElementById('name').value,
            code: document.getElementById('code').value,
            description: document.getElementById('description').value
        };

        try {
            await api.createDepartment(data);
            this.closeModal();
            this.showAlert('Department created successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to create department: ${error.message}`, 'danger');
            return;
        } finally {
            form.dataset.submitting = 'false';
            if (submitButton) submitButton.disabled = false;
        }

        const dashboard = AdminDashboard.instance;
        if (dashboard) {
            try {
                await dashboard.loadDepartments(true);
            } catch (error) {
                console.error('Department saved, but refresh failed:', error);
            }
        }
    }

    static async submitProgram(e) {
        e.preventDefault();
        const form = e.currentTarget;
        if (form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        const dashboard = AdminDashboard.instance;
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        const data = {
            name: document.getElementById('name').value,
            code: document.getElementById('code').value,
            department_id: parseInt(document.getElementById('department_id').value),
            duration_years: parseInt(document.getElementById('duration_years').value),
            description: document.getElementById('description').value
        };

        try {
            await api.createProgram(data);
            this.closeModal();
            this.showAlert(`Program ${data.name} registered successfully.`, 'success');
        } catch (error) {
            this.showAlert(`Failed to create program: ${error.message}`, 'danger');
            return;
        } finally {
            form.dataset.submitting = 'false';
            if (submitButton) submitButton.disabled = false;
        }

        if (dashboard) {
            try {
                await dashboard.loadPrograms();
                await dashboard.loadStatistics();
            } catch (refreshError) {
                console.error('Program created, but dashboard refresh failed:', refreshError);
            }
        }
    }

    static async submitCourse(e) {
        e.preventDefault();
        const form = e.currentTarget;
        if (form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        const dashboard = AdminDashboard.instance;
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        const data = {
            code: document.getElementById('code').value,
            name: document.getElementById('name').value,
            program_id: parseInt(document.getElementById('program_id').value),
            credits: parseInt(document.getElementById('credits').value),
            description: document.getElementById('description').value
        };

        try {
            await api.createCourse(data);
            this.closeModal();
            this.showAlert(`Course ${data.name} created successfully.`, 'success');
        } catch (error) {
            this.showAlert(`Failed to create course: ${error.message}`, 'danger');
            return;
        } finally {
            form.dataset.submitting = 'false';
            if (submitButton) submitButton.disabled = false;
        }

        if (dashboard) {
            try {
                await dashboard.loadCourses();
                await dashboard.loadStatistics();
            } catch (refreshError) {
                console.error('Course created, but dashboard refresh failed:', refreshError);
            }
        }
    }

    /**
     * Submit student form
     */
    static async submitStudent(e) {
        e.preventDefault();
        const form = e.currentTarget;
        if (form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        const data = {
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            email: document.getElementById('email').value,
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            student_id: document.getElementById('student_id').value,
            program_id: parseInt(document.getElementById('program_id').value),
            department_id: parseInt(document.getElementById('department_id').value)
        };

        try {
            await api.registerStudent(data);
            this.closeModal();
            this.showAlert('Student registered. They must change the temporary password at first login.', 'success');
        } catch (error) {
            this.showAlert(`Failed to register student: ${error.message}`, 'danger');
            return;
        } finally {
            form.dataset.submitting = 'false';
            if (submitButton) submitButton.disabled = false;
        }

        const dashboard = AdminDashboard.instance;
        if (dashboard) {
            try {
                await dashboard.loadStudents(true);
            } catch (error) {
                console.error('Student saved, but refresh failed:', error);
            }
        }
    }

    /**
     * Submit lecturer form
     */
    static async submitLecturer(e) {
        e.preventDefault();
        const form = e.currentTarget;
        if (form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
        }
        const data = {
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            email: document.getElementById('email').value,
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            lecturer_id: document.getElementById('lecturer_id').value,
            specialization: document.getElementById('specialization').value,
            department_id: parseInt(document.getElementById('department_id').value)
        };

        try {
            await api.registerLecturer(data);
            this.closeModal();
            this.showAlert('Lecturer registered. They must change the temporary password at first login.', 'success');
        } catch (error) {
            this.showAlert(`Failed to register lecturer: ${error.message}`, 'danger');
            return;
        } finally {
            form.dataset.submitting = 'false';
            if (submitButton) {
                submitButton.disabled = false;
            }
        }

        const dashboard = AdminDashboard.instance;
        if (dashboard) {
            try {
                await dashboard.loadLecturers(true);
            } catch (error) {
                console.error('Lecturer saved, but refresh failed:', error);
            }
        }
    }

    /**
     * Delete operations
     */
    static async editDepartment(id) {
        try {
            const response = await api.getDepartment(id);
            const department = response.data;
            const name = prompt('Department name:', department.name);
            if (name === null) return;
            const code = prompt('Department code:', department.code);
            if (code === null) return;
            const description = prompt('Description:', department.description || '');
            if (description === null) return;
            await api.updateDepartment(id, { name, code, description });
            await AdminDashboard.instance.loadDepartments();
            this.showAlert('Department updated successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to update department: ${error.message}`, 'danger');
        }
    }

    static async editProgram(id) {
        try {
            const response = await api.getProgram(id);
            const program = response.data;
            const name = prompt('Program name:', program.name);
            if (name === null) return;
            const code = prompt('Program code:', program.code);
            if (code === null) return;
            const durationYears = prompt('Duration in years:', program.duration_years);
            if (durationYears === null) return;
            const description = prompt('Description:', program.description || '');
            if (description === null) return;
            await api.updateProgram(id, {
                name,
                code,
                duration_years: parseInt(durationYears),
                description
            });
            await AdminDashboard.instance.loadPrograms();
            this.showAlert('Program updated successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to update program: ${error.message}`, 'danger');
        }
    }

    static async editCourse(id) {
        try {
            const response = await api.getCourse(id);
            const course = response.data;
            const name = prompt('Course name:', course.name);
            if (name === null) return;
            const code = prompt('Course code:', course.code);
            if (code === null) return;
            const credits = prompt('Credits:', course.credits);
            if (credits === null) return;
            const description = prompt('Description:', course.description || '');
            if (description === null) return;
            await api.updateCourse(id, {
                name,
                code,
                credits: parseInt(credits),
                description
            });
            await AdminDashboard.instance.loadCourses();
            this.showAlert('Course updated successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to update course: ${error.message}`, 'danger');
        }
    }

    static async editStudent(id) {
        try {
            const response = await api.getStudent(id);
            const student = response.data;
            const programId = prompt('Program ID:', student.program_id);
            if (programId === null) return;
            const departmentId = prompt('Department ID:', student.department_id);
            if (departmentId === null) return;
            await api.updateStudent(id, {
                program_id: parseInt(programId),
                department_id: parseInt(departmentId)
            });
            await AdminDashboard.instance.loadStudents();
            this.showAlert('Student updated successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to update student: ${error.message}`, 'danger');
        }
    }

    static async editLecturer(id) {
        try {
            const response = await api.getLecturer(id);
            const lecturer = response.data;
            const specialization = prompt('Specialization:', lecturer.specialization || '');
            if (specialization === null) return;
            const departmentId = prompt('Department ID:', lecturer.department_id);
            if (departmentId === null) return;
            await api.updateLecturer(id, {
                specialization,
                department_id: parseInt(departmentId)
            });
            await AdminDashboard.instance.loadLecturers();
            this.showAlert('Lecturer updated successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to update lecturer: ${error.message}`, 'danger');
        }
    }

    static async deleteDepartment(id) {
        if (!confirm('Are you sure you want to delete this department?')) return;
        try {
            await api.deleteDepartment(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                await dashboard.loadDepartments();
                await dashboard.loadStatistics();
            }
            this.showAlert('Department deleted successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    static async deleteStudent(id) {
        if (!confirm('Are you sure you want to delete this student?')) return;
        try {
            await api.deleteStudent(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                await dashboard.loadStudents();
                await dashboard.loadStatistics();
            }
            this.showAlert('Student deleted successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    static async deleteLecturer(id) {
        if (!confirm('Are you sure you want to delete this lecturer?')) return;
        try {
            await api.deleteLecturer(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                await dashboard.loadLecturers();
                await dashboard.loadStatistics();
            }
            this.showAlert('Lecturer deleted successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    static async deleteProgram(id) {
        if (!confirm('Are you sure?')) return;
        try {
            await api.deleteProgram(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                await dashboard.loadPrograms();
                await dashboard.loadStatistics();
            }
            this.showAlert('Program deleted successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    static async deleteCourse(id) {
        if (!confirm('Are you sure?')) return;
        try {
            await api.deleteCourse(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                try {
                    await dashboard.loadCourses();
                    await dashboard.loadStatistics();
                } catch (refreshError) {
                    console.error('Course deleted, but dashboard refresh failed:', refreshError);
                }
            }
            this.showAlert('Course deleted successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    static async deleteUser(id) {
        if (!confirm('Are you sure?')) return;
        try {
            await api.deleteUser(id);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                await dashboard.loadUsers();
                await dashboard.loadStatistics();
            }
            this.showAlert('User deleted successfully', 'success');
        } catch (error) {
            this.showAlert(`Failed to delete: ${error.message}`, 'danger');
        }
    }

    /**
     * Toggle user status
     */
    // ==================== Reports Functions ====================

    static async populateReportSelects() {
        try {
            // Populate course select for reports
            const courseResponse = await api.getAllCourses();
            if (courseResponse && courseResponse.data) {
                const courseSelect = document.getElementById('report-course-select');
                courseSelect.innerHTML = '<option value="">Choose a course...</option>' +
                    courseResponse.data.map(c => `<option value="${c.id}">${c.code} - ${c.name}</option>`).join('');
            }

            // Populate student select
            const studentResponse = await api.getAllStudents();
            if (studentResponse && studentResponse.data) {
                const studentSelect = document.getElementById('report-student-select');
                studentSelect.innerHTML = '<option value="">Choose a student...</option>' +
                    studentResponse.data.map(s => {
                        const firstName = s.user?.first_name || s.first_name || '';
                        const lastName = s.user?.last_name || s.last_name || '';
                        return `<option value="${s.id}">${s.student_id || s.id_num || s.id} - ${firstName} ${lastName}</option>`;
                    }).join('');
            }

            // Populate department select
            const deptResponse = await api.getAllDepartments();
            if (deptResponse && deptResponse.data) {
                const deptSelect = document.getElementById('report-dept-select');
                deptSelect.innerHTML = '<option value="">Choose a department...</option>' +
                    deptResponse.data.map(d => `<option value="${d.id}">${d.code} - ${d.name}</option>`).join('');
            }
        } catch (error) {
            console.error('Error populating report selects:', error);
        }
    }

    static async exportCourseReportCSV() {
        const courseId = document.getElementById('report-course-select').value;
        if (!courseId) {
            this.showAlert('Please select a course', 'warning');
            return;
        }
        try {
            await api.exportAttendanceCSV(courseId);
            this.showAlert('CSV report downloaded successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to download CSV: ${error.message}`, 'danger');
        }
    }

    static async exportCourseReportPDF() {
        const courseId = document.getElementById('report-course-select').value;
        if (!courseId) {
            this.showAlert('Please select a course', 'warning');
            return;
        }
        try {
            await api.exportAttendancePDF(courseId);
            this.showAlert('PDF report downloaded successfully.', 'success');
        } catch (error) {
            this.showAlert(`Failed to download PDF: ${error.message}`, 'danger');
        }
    }

    static async viewStudentReport() {
        const studentId = document.getElementById('report-student-select').value;
        if (!studentId) {
            this.showAlert('Please select a student', 'warning');
            return;
        }

        try {
            const response = await api.getStudentAttendanceReport(studentId);
            if (response && response.data) {
                this.displayReportData(response.data, 'Student Attendance Report');
            }
        } catch (error) {
            this.showAlert('Error loading student report', 'error');
        }
    }

    static async viewDepartmentReport() {
        const deptId = document.getElementById('report-dept-select').value;
        if (!deptId) {
            this.showAlert('Please select a department', 'warning');
            return;
        }

        try {
            const response = await api.getDepartmentAttendanceReport(deptId);
            if (response && response.data) {
                this.displayReportData(response.data, 'Department Attendance Report');
            }
        } catch (error) {
            this.showAlert('Error loading department report', 'error');
        }
    }

    static async viewDateRangeReport() {
        const startDate = document.getElementById('report-start-date').value;
        const endDate = document.getElementById('report-end-date').value;

        if (!startDate || !endDate) {
            this.showAlert('Please select both start and end dates', 'warning');
            return;
        }

        try {
            const response = await api.getStatisticsByDateRange(startDate, endDate);
            if (response && response.data) {
                this.displayReportData(response.data, 'Date Range Report');
            }
        } catch (error) {
            this.showAlert('Error loading date range report', 'error');
        }
    }

    static async viewLowAttendanceStudents() {
        const threshold = document.getElementById('attendance-threshold').value || 75;

        try {
            const response = await api.getLowAttendanceStudents(threshold);
            if (response && response.data) {
                this.renderLowAttendanceTable(response.data);
            }
        } catch (error) {
            this.showAlert('Error loading low attendance students', 'error');
        }
    }

    static renderLowAttendanceTable(data) {
        const tbody = document.querySelector('#low-attendance-table tbody');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No students below threshold</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(item => {
            const status = item.average_attendance >= 75 ? 'Good' : 
                          item.average_attendance >= 50 ? 'Low' : 'Critical';
            const statusClass = status === 'Good' ? 'status-active' : 'status-inactive';

            return `
                <tr>
                    <td>${item.student_id || item.id_num || '-'}</td>
                    <td>${item.student_name || [item.first_name, item.last_name].filter(Boolean).join(' ') || '-'}</td>
                    <td>${item.email}</td>
                    <td>${(item.average_attendance || 0).toFixed(1)}%</td>
                    <td><span class="${statusClass}">${status}</span></td>
                </tr>
            `;
        }).join('');
    }

    static displayReportData(data, title) {
        alert(`${title}:\n${JSON.stringify(data, null, 2)}`);
    }

    // ==================== Analytics Functions ====================

    static async loadAnalytics() {
        try {
            // Load system statistics
            const statsResponse = await api.getSummaryStatistics();
            if (statsResponse && statsResponse.data) {
                const stats = statsResponse.data;
                document.getElementById('metric-sessions').textContent = stats.total_sessions || 0;
                document.getElementById('metric-checkins').textContent = stats.total_attendance_records || 0;
                document.getElementById('metric-avg').textContent = (stats.average_attendance || 0).toFixed(1) + '%';
                
                let warningsCount = 0;
                if (stats.warnings_by_level) {
                    warningsCount = (stats.warnings_by_level.low || 0) + (stats.warnings_by_level.critical || 0);
                }
                document.getElementById('metric-warnings').textContent = warningsCount;
            }

            // Load course statistics
            const courseStatsResponse = await api.getStatisticsByCourse();
            if (courseStatsResponse && courseStatsResponse.data) {
                this.renderCourseStats(courseStatsResponse.data);
            }

            // Load student statistics
            const studentStatsResponse = await api.getStatisticsByStudent();
            if (studentStatsResponse && studentStatsResponse.data) {
                this.renderStudentStats(studentStatsResponse.data);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    static renderCourseStats(data) {
        const tbody = document.querySelector('#course-stats-table tbody');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No course data</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(course => {
            const lowCount = Math.round((course.enrolled_students || 0) * (1 - (course.average_attendance || 0) / 100));
            
            return `
                <tr>
                    <td>${course.course_code || 'N/A'}</td>
                    <td>${course.course_name || 'N/A'}</td>
                    <td>${course.enrolled_students || 0}</td>
                    <td>${(course.average_attendance || 0).toFixed(1)}%</td>
                    <td>${course.total_sessions || 0}</td>
                    <td>${lowCount}</td>
                </tr>
            `;
        }).join('');
    }

    static renderStudentStats(data) {
        const tbody = document.querySelector('#student-stats-table tbody');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No student data</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(student => {
            let lowCount = 0;
            let criticalCount = 0;

            if (student.course_breakdown) {
                student.course_breakdown.forEach(course => {
                    if (course.average_attendance < 75 && course.average_attendance >= 50) {
                        lowCount++;
                    } else if (course.average_attendance < 50) {
                        criticalCount++;
                    }
                });
            }

            return `
                <tr>
                    <td>${student.student_id || student.student_id_num || student.id || '-'}</td>
                    <td>${student.student_name || [student.first_name, student.last_name].filter(Boolean).join(' ') || '-'}</td>
                    <td>${student.enrolled_courses || 0}</td>
                    <td>${(student.average_attendance || 0).toFixed(1)}%</td>
                    <td>${lowCount}</td>
                    <td>${criticalCount}</td>
                </tr>
            `;
        }).join('');
    }

    static async toggleUserStatus(id, isActive) {
        try {
            await api.toggleUserStatus(id, isActive);
            const dashboard = AdminDashboard.instance;
            if (dashboard) {
                try {
                    await dashboard.loadUsers();
                } catch (refreshError) {
                    console.error('User status updated, but users refresh failed:', refreshError);
                }
            }
            this.showAlert('User status updated', 'success');
        } catch (error) {
            this.showAlert(`Failed to update: ${error.message}`, 'danger');
        }
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (!localStorage.getItem('access_token')) {
        window.location.href = 'login.html';
        return;
    }

    window.admin = new AdminDashboard();
});


// ==================== Assignment Functions ====================

AdminDashboard.prototype.addAssignmentModals = function() {
    // Add assignment and enrollment modal handling
    const originalOpenModal = this.openModal.bind(this);
    this.openModal = function(type) {
        if (type === 'assignment') {
            const form = document.getElementById('modal-form');
            const title = document.getElementById('modal-title');
            title.textContent = 'Assign Lecturer to Course';
            form.innerHTML = `
                <div class="form-row">
                    <div class="form-group">
                        <label>Course *</label>
                        <select id="course_id" required>
                            <option value="">Select Course</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Lecturer *</label>
                        <select id="lecturer_id" required>
                            <option value="">Select Lecturer</option>
                        </select>
                    </div>
                </div>
                <div class="form-buttons">
                    <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Assign</button>
                </div>
            `;
            this.populateAssignmentSelects();
            form.onsubmit = (e) => this.submitAssignment(e);
            this.modal.classList.add('active');
        } else if (type === 'enrollment') {
            const form = document.getElementById('modal-form');
            const title = document.getElementById('modal-title');
            title.textContent = 'Enroll Student in Course';
            form.innerHTML = `
                <div class="form-row">
                    <div class="form-group">
                        <label>Student *</label>
                        <select id="student_id" required>
                            <option value="">Select Student</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Course *</label>
                        <select id="course_id" required>
                            <option value="">Select Course</option>
                        </select>
                    </div>
                </div>
                <div class="form-buttons">
                    <button type="button" class="btn btn-secondary" onclick="AdminDashboard.closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Enroll</button>
                </div>
            `;
            this.populateEnrollmentSelects();
            form.onsubmit = (e) => this.submitEnrollment(e);
            this.modal.classList.add('active');
        } else {
            originalOpenModal(type);
        }
    };
};

AdminDashboard.populateAssignmentSelects = async function() {
    try {
        const courses = await api.getCourses();
        const lecturers = await api.getLecturers();

        const courseSelect = document.getElementById('course_id');
        (courses.data || []).forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = `${course.code} - ${course.name}`;
            courseSelect.appendChild(option);
        });

        const lecturerSelect = document.getElementById('lecturer_id');
        (lecturers.data || []).forEach(lecturer => {
            const option = document.createElement('option');
            option.value = lecturer.id;
            option.textContent = lecturer.user
                ? `${lecturer.user.first_name} ${lecturer.user.last_name}`
                : lecturer.lecturer_id;
            lecturerSelect.appendChild(option);
        });
    } catch (error) {
        AdminDashboard.showAlert(`Failed to load dropdown data: ${error.message}`, 'danger');
    }
};

AdminDashboard.populateEnrollmentSelects = async function() {
    try {
        const students = await api.getStudents();
        const courses = await api.getCourses();

        const studentSelect = document.getElementById('student_id');
        students.data.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = `${student.student_id} - ${student.user.first_name} ${student.user.last_name}`;
            studentSelect.appendChild(option);
        });

        const courseSelect = document.getElementById('course_id');
        courses.data.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = `${course.code} - ${course.name}`;
            courseSelect.appendChild(option);
        });
    } catch (error) {
        this.showAlert(`Failed to load dropdown data: ${error.message}`, 'danger');
    }
};

AdminDashboard.submitAssignment = async function(e) {
    e.preventDefault();
    const form = e.currentTarget;
    if (form.dataset.submitting === 'true') return;
    form.dataset.submitting = 'true';
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) submitButton.disabled = true;
    const data = {
        course_id: parseInt(document.getElementById('course_id').value),
        lecturer_id: parseInt(document.getElementById('lecturer_id').value)
    };

    try {
        await api.assignLecturerToCourse(data);
        this.closeModal();
        this.showAlert('Lecturer assigned to course successfully', 'success');
    } catch (error) {
        this.showAlert(`Failed to assign: ${error.message}`, 'danger');
        return;
    } finally {
        form.dataset.submitting = 'false';
        if (submitButton) submitButton.disabled = false;
    }

    const dashboard = AdminDashboard.instance;
    if (dashboard) {
        try {
            await dashboard.loadAssignments(true);
        } catch (error) {
            console.error('Assignment saved, but refresh failed:', error);
        }
    }
};

AdminDashboard.submitEnrollment = async function(e) {
    e.preventDefault();
    const form = e.currentTarget;
    if (form.dataset.submitting === 'true') return;
    form.dataset.submitting = 'true';
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) submitButton.disabled = true;
    const studentSelect = document.getElementById('student_id');
    const courseSelect = document.getElementById('course_id');
    const data = {
        student_id: parseInt(studentSelect.value),
        course_id: parseInt(courseSelect.value)
    };
    const studentName = studentSelect.options[studentSelect.selectedIndex].textContent;
    const courseName = courseSelect.options[courseSelect.selectedIndex].textContent;

    try {
        await api.enrollStudentInCourse(data);
        this.closeModal();
        this.showAlert(`${studentName} has been enrolled in ${courseName}.`, 'success');
    } catch (error) {
        this.showAlert(`Failed to enroll: ${error.message}`, 'danger');
        return;
    } finally {
        form.dataset.submitting = 'false';
        if (submitButton) submitButton.disabled = false;
    }

    const dashboard = AdminDashboard.instance;
    if (dashboard) {
        try {
            await dashboard.loadEnrollments(true);
        } catch (error) {
            console.error('Enrollment saved, but refresh failed:', error);
        }
    }
};

AdminDashboard.removeAssignment = async function(id) {
    if (!confirm('Are you sure?')) return;
    try {
        await api.removeCourseLecturer(id);
        new AdminDashboard().showAlert('Assignment removed', 'success');
        new AdminDashboard().loadAssignments();
    } catch (error) {
        new AdminDashboard().showAlert(`Failed to remove: ${error.message}`, 'danger');
    }
};

AdminDashboard.removeEnrollment = async function(id) {
    if (!confirm('Are you sure?')) return;
    try {
        await api.removeStudentCourse(id);
        new AdminDashboard().showAlert('Enrollment removed', 'success');
        new AdminDashboard().loadEnrollments();
    } catch (error) {
        new AdminDashboard().showAlert(`Failed to remove: ${error.message}`, 'danger');
    }
};
