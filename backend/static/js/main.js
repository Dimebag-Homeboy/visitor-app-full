import { login, logout, fetchWithAuth } from './api.js';
import { showNotification, withLoading } from './ui.js';
import { loadVisitors, setCurrentLimit } from './visitors.js';
import { initModals } from './modals.js';
import { initTheme } from './theme.js';

let currentUserRole = '';
let currentUserFullName = '';

async function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) return false;
    try {
        const response = await fetchWithAuth('/users/me');
        if (response.ok) {
            const user = await response.json();
            currentUserRole = user.role;
            currentUserFullName = user.full_name;
            showMainScreen();
            await loadVisitors(true);
            return true;
        } else {
            logout();
            return false;
        }
    } catch (err) {
        logout();
        return false;
    }
}

function showMainScreen() {
    document.getElementById('loginBlock').classList.add('hidden');
    document.getElementById('mainBlock').classList.remove('hidden');
    const userRoleLabel = document.getElementById('userRoleLabel');
    if (userRoleLabel) {
        if (currentUserRole === 'admin') userRoleLabel.innerText = 'Админ';
        else if (currentUserRole === 'secretary') userRoleLabel.innerText = 'Секретарь';
        else if (currentUserRole === 'guard') userRoleLabel.innerText = 'Охрана';
    }
    const manageUsersBtn = document.getElementById('manageUsersBtn');
    const reportBtn = document.getElementById('reportBtn');
    const viewLogsBtn = document.getElementById('viewLogsBtn');

    if (manageUsersBtn) {
        if (currentUserRole === 'admin') {
            manageUsersBtn.classList.remove('hidden');
            manageUsersBtn.style.display = '';
        } else {
            manageUsersBtn.classList.add('hidden');
            manageUsersBtn.style.display = 'none';
        }
    }
    if (reportBtn) {
        if (currentUserRole === 'guard') {
            reportBtn.classList.add('hidden');
            reportBtn.style.display = 'none';
        } else {
            reportBtn.classList.remove('hidden');
            reportBtn.style.display = '';
        }
    }
    if (viewLogsBtn) {
        if (currentUserRole === 'admin') {
            viewLogsBtn.classList.remove('hidden');
            viewLogsBtn.style.display = '';
        } else {
            viewLogsBtn.classList.add('hidden');
            viewLogsBtn.style.display = 'none';
        }
    }
}

async function onLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    await withLoading(loginBtn, 'Войти', async () => {
        try {
            const data = await login(username, password);
            currentUserRole = data.role;
            currentUserFullName = data.full_name;
            showMainScreen();
            await loadVisitors(true);
            showNotification(`Добро пожаловать, ${currentUserFullName}!`, 'success');
        } catch (err) {
            showNotification(err.message, 'error');
            document.getElementById('loginError').innerText = err.message;
        }
    });
}

function onLogout() {
    logout();
}

async function onSubmitVisitor(e) {
    e.preventDefault();
    const full_name = document.getElementById('full_name').value.trim();
    const company = document.getElementById('company').value.trim();
    const whom_visit = document.getElementById('whom_visit').value.trim();
    const purpose = document.getElementById('purpose').value.trim();
    if (!full_name || !company || !whom_visit || !purpose) {
        showNotification('Заполните все поля', 'error');
        return;
    }
    const nameRegex = /^[а-яА-ЯёЁa-zA-Z][а-яА-ЯёЁa-zA-Z\s\-\.]+$/;
    if (!nameRegex.test(full_name) || !nameRegex.test(whom_visit) || !nameRegex.test(purpose)) {
        showNotification('Поля содержат недопустимые символы', 'error');
        return;
    }
    const submitBtn = document.querySelector('#visitorForm button[type="submit"]');
    await withLoading(submitBtn, 'Зарегистрировать вход', async () => {
        const response = await fetchWithAuth('/visitors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name, company, whom_visit, purpose })
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Ошибка регистрации');
        }
        document.getElementById('visitorForm').reset();
        await loadVisitors(true);
        showNotification('Посетитель зарегистрирован', 'success');
    });
}

async function onReport() {
    const role = localStorage.getItem('role');
    if (role === 'guard') {
        showNotification('У вас нет прав на выгрузку отчёта', 'error');
        return;
    }
    const reportBtn = document.getElementById('reportBtn');
    await withLoading(reportBtn, '📊 Выгрузить отчёт Excel', async () => {
        const search = document.getElementById('searchInput')?.value || '';
        const hideCompleted = document.getElementById('hideCompletedCheckbox')?.checked || false;
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (hideCompleted) params.append('hide_completed', 'true');
        const response = await fetchWithAuth(`/report/excel?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка при выгрузке отчёта');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'visitors_report.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showNotification('Отчёт успешно выгружен', 'success');
    });
}

function debounce(fn, delay) {
    let timer;
    return function() {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, arguments), delay);
    };
}

function initPasswordToggle() {
    const togglePassword = document.getElementById('togglePassword');
    const passwordField = document.getElementById('password');
    if (togglePassword && passwordField) {
        togglePassword.addEventListener('click', () => {
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            const icon = togglePassword.querySelector('i');
            if (icon) icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
        });
    }
}

function initEventListeners() {
    document.getElementById('loginBtn').addEventListener('click', onLogin);
    document.getElementById('logoutBtn').addEventListener('click', onLogout);
    document.getElementById('visitorForm').addEventListener('submit', onSubmitVisitor);
    document.getElementById('reportBtn').addEventListener('click', onReport);
    document.getElementById('hideCompletedCheckbox')?.addEventListener('change', () => loadVisitors(true));
    document.getElementById('searchInput')?.addEventListener('input', debounce(() => loadVisitors(true), 400));
    document.getElementById('dateFilter')?.addEventListener('change', () => loadVisitors(true));
    document.getElementById('limitSelect')?.addEventListener('change', (e) => {
        setCurrentLimit(parseInt(e.target.value));
        loadVisitors(true);
    });
}

async function init() {
    initTheme();
    initModals();
    initPasswordToggle();
    initEventListeners();
    const token = localStorage.getItem('token');
    if (token) {
        const isValid = await checkAuth();
        if (!isValid) {
            document.getElementById('loginBlock').classList.remove('hidden');
            document.getElementById('mainBlock').classList.add('hidden');
        }
    } else {
        document.getElementById('loginBlock').classList.remove('hidden');
        document.getElementById('mainBlock').classList.add('hidden');
    }
}

init();