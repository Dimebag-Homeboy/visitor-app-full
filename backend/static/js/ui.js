export function showNotification(message, type = 'error') {
    const container = document.getElementById('notification-container') || (() => {
        const div = document.createElement('div');
        div.id = 'notification-container';
        div.className = 'notification-container';
        document.body.appendChild(div);
        return div;
    })();
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${escapeHtml(message)}</span>
        <button class="notification-close">&times;</button>
    `;
    container.appendChild(notification);
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => notification.remove());
    setTimeout(() => notification.remove(), 5000);
}

export function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

export function withLoading(button, originalText, asyncFunc) {
    if (!button) return asyncFunc();
    const original = originalText || button.innerText;
    button.disabled = true;
    button.innerText = '⏳ Загрузка...';
    return asyncFunc().finally(() => {
        button.disabled = false;
        button.innerText = original;
    });
}

export function renderPagination(currentPage, totalItems, limit, onPageChange) {
    const totalPages = Math.ceil(totalItems / limit);
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    container.style.display = totalPages > 1 ? 'flex' : 'none';
    const pageNumbersSpan = document.getElementById('pageNumbers');
    if (pageNumbersSpan) pageNumbersSpan.innerText = `Страница ${currentPage} из ${totalPages}`;
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages;
    
    // Удаляем старые обработчики, чтобы не навешивать много
    const newPrev = prevBtn.cloneNode(true);
    const newNext = nextBtn.cloneNode(true);
    if (prevBtn && prevBtn.parentNode) {
        prevBtn.parentNode.replaceChild(newPrev, prevBtn);
        newPrev.addEventListener('click', () => { if (currentPage > 1) onPageChange(currentPage - 1); });
    }
    if (nextBtn && nextBtn.parentNode) {
        nextBtn.parentNode.replaceChild(newNext, nextBtn);
        newNext.addEventListener('click', () => { if (currentPage < totalPages) onPageChange(currentPage + 1); });
    }
}

export function updateStats(visitors) {
    const statsBlock = document.getElementById('statsBlock');
    if (!statsBlock) return;
    const total = visitors.length;
    const active = visitors.filter(v => v.check_out === null).length;
    const completed = total - active;
    const today = new Date();
    today.setHours(0,0,0,0);
    const todayCount = visitors.filter(v => {
        const d = new Date(v.check_in);
        return d >= today;
    }).length;
    statsBlock.innerHTML = `
        <div class="stat-card"><i class="fas fa-users"></i><strong>Всего посетителей:</strong><span>${total}</span></div>
        <div class="stat-card"><i class="fas fa-building"></i><strong>Сейчас в здании:</strong><span>${active}</span></div>
        <div class="stat-card"><i class="fas fa-check-circle"></i><strong>Завершённых визитов:</strong><span>${completed}</span></div>
        <div class="stat-card"><i class="fas fa-calendar-day"></i><strong>Посетителей сегодня:</strong><span>${todayCount}</span></div>
    `;
}