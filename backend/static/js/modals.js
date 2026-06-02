import { fetchWithAuth } from './api.js';
import { showNotification, withLoading, escapeHtml } from './ui.js';

export function initModals() {
    const manageUsersBtn = document.getElementById('manageUsersBtn');
    const userModal = document.getElementById('userModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const createUserBtn = document.getElementById('createUserBtn');
    const viewLogsBtn = document.getElementById('viewLogsBtn');
    const logsModal = document.getElementById('logsModal');
    const closeLogsModalBtn = document.getElementById('closeLogsModalBtn');

    if (manageUsersBtn) manageUsersBtn.addEventListener('click', openUserModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', () => userModal.style.display = 'none');
    if (createUserBtn) createUserBtn.addEventListener('click', onCreateUser);
    if (viewLogsBtn) viewLogsBtn.addEventListener('click', openLogsModal);
    if (closeLogsModalBtn) closeLogsModalBtn.addEventListener('click', () => logsModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === userModal) userModal.style.display = 'none';
        if (e.target === logsModal) logsModal.style.display = 'none';
    });
}

async function openUserModal() {
    await loadUsersList();
    const modal = document.getElementById('userModal');
    if (modal) modal.style.display = 'flex';
}

async function loadUsersList() {
    const container = document.getElementById('usersListDiv');
    if (!container) return;
    container.innerHTML = 'Загрузка...';
    try {
        const response = await fetchWithAuth('/users');
        if (!response.ok) throw new Error('Ошибка загрузки пользователей');
        const users = await response.json();
        let html = '<table class="user-table"><thead><tr><th>ID</th><th>Логин</th><th>ФИО</th><th>Роль</th><th>Действия</th></tr></thead><tbody>';
        users.forEach(u => {
            html += `<tr>
                        <td>${u.id}</td>
                        <td>${escapeHtml(u.username)}</td>
                        <td>${escapeHtml(u.full_name)}</td>
                        <td><select class="role-select" data-id="${u.id}">
                                <option value="secretary" ${u.role==='secretary'?'selected':''}>Секретарь</option>
                                <option value="guard" ${u.role==='guard'?'selected':''}>Охранник</option>
                                <option value="admin" ${u.role==='admin'?'selected':''}>Администратор</option>
                            </select>
                        </td>
                        <td><button class="delete-user" data-id="${u.id}" ${u.username==='admin'?'disabled':''}>Удалить</button></td>
                      </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
        
        document.querySelectorAll('.role-select').forEach(sel => sel.addEventListener('change', async () => {
            await fetchWithAuth(`/users/${sel.dataset.id}/role?role=${sel.value}`, { method: 'PUT' });
            showNotification('Роль изменена', 'success');
            await loadUsersList();
        }));
        document.querySelectorAll('.delete-user').forEach(btn => {
            if (!btn.disabled) btn.addEventListener('click', async () => {
                if (confirm('Удалить пользователя?')) {
                    await fetchWithAuth(`/users/${btn.dataset.id}`, { method: 'DELETE' });
                    showNotification('Пользователь удалён', 'success');
                    await loadUsersList();
                }
            });
        });
    } catch (err) {
        container.innerHTML = 'Ошибка загрузки';
        showNotification('Не удалось загрузить список пользователей', 'error');
    }
}

async function onCreateUser() {
    const btn = document.getElementById('createUserBtn');
    await withLoading(btn, 'Создать', async () => {
        const username = document.getElementById('newUsername').value;
        const password = document.getElementById('newPassword').value;
        const full_name = document.getElementById('newFullName').value;
        const role = document.getElementById('newRole').value;
        if (!username || !password || !full_name) {
            showNotification('Заполните все поля', 'error');
            return;
        }
        const response = await fetchWithAuth('/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, full_name, role })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Ошибка создания');
        }
        showNotification('Пользователь создан', 'success');
        document.getElementById('newUsername').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('newFullName').value = '';
        await loadUsersList();
    });
}

async function openLogsModal() {
    const modal = document.getElementById('logsModal');
    if (!modal) return;
    const logsContent = document.getElementById('logsContent');
    logsContent.innerHTML = 'Загрузка...';
    try {
        const response = await fetchWithAuth('/logs?skip=0&limit=200');
        if (!response.ok) throw new Error('Ошибка загрузки логов');
        const data = await response.json();
        const logs = data.items || [];
        if (logs.length === 0) {
            logsContent.innerHTML = '<p>Логов пока нет</p>';
        } else {
            let html = '<table class="log-table"><thead><tr><th>Время</th><th>Пользователь</th><th>Действие</th><th>Детали</th></tr></thead><tbody>';
            logs.forEach(log => {
                html += `<tr>
                            <td>${new Date(log.timestamp).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' })}</td>
                            <td>${escapeHtml(log.username)}</td>
                            <td>${escapeHtml(log.action)}</td>
                            <td>${escapeHtml(log.details || '')}</td>
                          </tr>`;
            });
            html += '</tbody></table>';
            logsContent.innerHTML = html;
        }
        modal.style.display = 'flex';
    } catch (err) {
        logsContent.innerHTML = '<p>Ошибка загрузки логов</p>';
        showNotification('Не удалось загрузить логи', 'error');
    }
}