/**
 * STMS Government Portal — Authentication Module
 * Handles JWT auth with the FastAPI backend (v1 API)
 */

const API_BASE = '/api/v1';  // Versioned API

// ---- Token Management ----
function getToken() {
    return localStorage.getItem('stms_token');
}

function setToken(token) {
    localStorage.setItem('stms_token', token);
}

function clearToken() {
    localStorage.removeItem('stms_token');
}

function getUser() {
    try {
        const u = localStorage.getItem('stms_user');
        return u ? JSON.parse(u) : null;
    } catch { return null; }
}

function setUser(user) {
    localStorage.setItem('stms_user', JSON.stringify(user));
}

function clearUser() {
    localStorage.removeItem('stms_user');
}

function isAuthenticated() {
    return !!getToken();
}

function getCurrentUser() {
    return getUser();
}

// ---- Authenticated Fetch ----
async function authFetch(url, options = {}) {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');

    const headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 || response.status === 403) {
        logout();
        return response;
    }
    return response;
}

// ---- Login ----
async function login(email, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || data.detail || 'Login failed');
    }

    setToken(data.token);
    setUser(data.user);
    return data;
}

// ---- Register ----
async function register(name, email, password) {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || data.detail || 'Registration failed');
    }

    return data;
}

// ---- Logout ----
function logout() {
    // Fire-and-forget logout to backend
    const token = getToken();
    if (token) {
        fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
        }).catch(() => {});
    }
    clearToken();
    clearUser();
    window.location.href = 'govt-login.html';
}

// ---- Guard protected pages ----
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'govt-login.html';
        return false;
    }
    return true;
}

// ---- Show user info in navbar ----
function displayNavUser() {
    const user = getUser();
    const nameEl = document.getElementById('nav-user-name');
    const roleEl = document.getElementById('nav-user-role');
    if (user) {
        if (nameEl) nameEl.textContent = user.name || 'Officer';
        if (roleEl) roleEl.textContent = user.role || 'user';
    }
}
