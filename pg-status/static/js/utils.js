/**
 * StaySync — Utility Functions
 * API helpers with retry logic, toast creation, date formatting
 */

const MAX_RETRIES = 2;

async function apiPost(url, data = {}, retries = 0) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : ''
            },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        return json;
    } catch (err) {
        if (retries < MAX_RETRIES) {
            console.warn(`API retry ${retries + 1} for ${url}`);
            await new Promise(r => setTimeout(r, 1000 * (retries + 1)));
            return apiPost(url, data, retries + 1);
        }
        console.error('API call failed:', url, err);
        return { success: false, error: 'Network error. Please try again.', code: 0 };
    }
}

async function apiGet(url, retries = 0) {
    try {
        const res = await fetch(url);
        return await res.json();
    } catch (err) {
        if (retries < MAX_RETRIES) {
            await new Promise(r => setTimeout(r, 1000 * (retries + 1)));
            return apiGet(url, retries + 1);
        }
        return { success: false, error: 'Network error.', code: 0 };
    }
}

function showToast(type, title, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✅', warning: '⚠️', error: '❌', info: 'ℹ️' };
    const toasts = container.querySelectorAll('.toast');
    if (toasts.length >= 3) toasts[0].remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <span class="toast-close" onclick="this.parentElement.remove()">✕</span>
        <div class="toast-progress"></div>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

function timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
}

function formatCountdown(expiresAt) {
    const now = new Date();
    const target = new Date(expiresAt);
    const diff = target - now;
    if (diff <= 0) return 'Expired';

    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
}

function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN');
}
