let isRefreshing = false;
let refreshSubscribers = [];

function onTokenRefreshed(newToken) {
    refreshSubscribers.forEach(cb => cb(newToken));
    refreshSubscribers = [];
}

async function refreshAccessToken() {
    const response = await fetch('/refresh', {
        method: 'POST',
        credentials: 'include'
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Refresh failed');
    }
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('role', data.role);
    localStorage.setItem('fullName', data.full_name);
    return data.access_token;
}

export async function fetchWithAuth(url, options = {}) {
    const makeRequest = (tok) => fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${tok}`
        },
        credentials: 'include'
    });

    let response = await makeRequest(localStorage.getItem('token'));
    if (response.status !== 401) return response;

    if (isRefreshing) {
        const newToken = await new Promise(resolve => {
            refreshSubscribers.push(resolve);
        });
        return makeRequest(newToken);
    }

    isRefreshing = true;
    try {
        const newToken = await refreshAccessToken();
        onTokenRefreshed(newToken);
        return makeRequest(newToken);
    } catch (err) {
        refreshSubscribers.forEach(cb => cb(Promise.reject(err)));
        refreshSubscribers = [];
        throw err;
    } finally {
        isRefreshing = false;
    }
}

export async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const response = await fetch('/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
        credentials: 'include'
    });
    if (!response.ok) {
        let errorMsg = 'Неверный логин или пароль';
        try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorMsg;
        } catch(e) {}
        throw new Error(errorMsg);
    }
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('role', data.role);
    localStorage.setItem('fullName', data.full_name);
    return data;
}

export function logout() {
    fetch('/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('fullName');
    window.location.reload();
}