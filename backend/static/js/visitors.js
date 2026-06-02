import { fetchWithAuth } from './api.js';
import { showNotification, withLoading, renderPagination, updateStats } from './ui.js';
import { printPass } from './print.js';

let currentVisitors = [];
let currentPage = 1;
let currentLimit = 25;
let totalItems = 0;

export function getCurrentPage() { return currentPage; }
export function getCurrentLimit() { return currentLimit; }
export function setCurrentLimit(limit) { currentLimit = limit; }

export async function loadVisitors(reset = true, extraParams = {}) {
    if (reset) currentPage = 1;
    const skip = (currentPage - 1) * currentLimit;
    const params = new URLSearchParams({
        skip, limit: currentLimit,
        ...extraParams
    });
    const search = document.getElementById('searchInput')?.value || '';
    const hideCompleted = document.getElementById('hideCompletedCheckbox')?.checked || false;
    const dateFilter = document.getElementById('dateFilter')?.value || 'all';
    if (search) params.append('search', search);
    if (hideCompleted) params.append('hide_completed', 'true');
    const { dateFrom, dateTo } = getDateRange(dateFilter);
    if (dateFrom) params.append('date_from', dateFrom.toISOString());
    if (dateTo) params.append('date_to', dateTo.toISOString());

    try {
        const response = await fetchWithAuth(`/visitors?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        const data = await response.json();
        currentVisitors = data.items || [];
        totalItems = data.total || currentVisitors.length;
        renderTable(currentVisitors);
        updateStats(currentVisitors);
        renderPagination(currentPage, totalItems, currentLimit, (newPage) => {
            currentPage = newPage;
            loadVisitors(false, extraParams);
        });
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

function getDateRange(filterValue) {
    const now = new Date();
    const toUTCDate = (localDate) => new Date(Date.UTC(
        localDate.getFullYear(), localDate.getMonth(), localDate.getDate(),
        localDate.getHours(), localDate.getMinutes(), localDate.getSeconds()
    ));
    if (filterValue === 'today') {
        const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
        return { dateFrom: toUTCDate(start), dateTo: toUTCDate(end) };
    } else if (filterValue === 'week') {
        const start = new Date(now);
        start.setDate(now.getDate() - 7);
        start.setHours(0,0,0,0);
        const end = new Date(now);
        end.setHours(23,59,59,999);
        return { dateFrom: toUTCDate(start), dateTo: toUTCDate(end) };
    } else if (filterValue === 'month') {
        const start = new Date(now.getFullYear(), now.getMonth(), 1);
        const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
        return { dateFrom: toUTCDate(start), dateTo: toUTCDate(end) };
    }
    return { dateFrom: null, dateTo: null };
}

function renderTable(visitors) {
    const tbody = document.getElementById('visitorsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    visitors.forEach(v => {
        const row = tbody.insertRow();
        row.insertCell(0).innerText = v.id;
        row.cells[0].setAttribute('data-label', 'ID');
        row.insertCell(1).innerText = v.full_name;
        row.cells[1].setAttribute('data-label', 'ФИО');
        row.insertCell(2).innerText = v.company;
        row.cells[2].setAttribute('data-label', 'Компания');
        row.insertCell(3).innerText = v.whom_visit;
        row.cells[3].setAttribute('data-label', 'К кому');
        row.insertCell(4).innerText = v.purpose;
        row.cells[4].setAttribute('data-label', 'Цель');
        const checkInLocal = new Date(v.check_in).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
        row.insertCell(5).innerText = checkInLocal;
        row.cells[5].setAttribute('data-label', 'Время прихода');
        const cellCheckOut = row.insertCell(6);
        if (v.check_out) {
            const checkOutLocal = new Date(v.check_out).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
            cellCheckOut.innerText = checkOutLocal;
        } else {
            cellCheckOut.innerText = 'На предприятии';
            cellCheckOut.style.color = 'green';
            cellCheckOut.style.fontWeight = 'bold';
        }
        cellCheckOut.setAttribute('data-label', 'Время ухода');
        const actionCell = row.insertCell(7);
        actionCell.setAttribute('data-label', 'Действие');
        if (!v.check_out) {
            const role = localStorage.getItem('role');
            if (role === 'guard' || role === 'admin') {
                const checkoutBtn = document.createElement('button');
                checkoutBtn.innerText = 'Отметить выход';
                checkoutBtn.classList.add('checkout-btn');
                checkoutBtn.onclick = async () => {
                    await withLoading(checkoutBtn, 'Отметить выход', () => markCheckout(v.id));
                };
                actionCell.appendChild(checkoutBtn);
            }
            const printBtn = document.createElement('button');
            printBtn.innerText = 'Печать пропуска';
            printBtn.classList.add('print-btn');
            printBtn.onclick = () => printPass(v);
            actionCell.appendChild(printBtn);
        } else {
            actionCell.innerText = 'Завершён';
        }
    });
}

async function markCheckout(id) {
    if (!confirm('Вы уверены?')) return;
    try {
        const response = await fetchWithAuth(`/visitors/${id}/checkout`, { method: 'PUT' });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Ошибка при отметке выхода');
        }
        await loadVisitors(true);
        showNotification('Выход успешно отмечен', 'success');
    } catch (err) {
        showNotification(err.message, 'error');
    }
}