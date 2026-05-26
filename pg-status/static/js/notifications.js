/**
 * StaySync — Notifications
 * Bell dropdown, badge count, mark read
 */

function toggleNotifications() {
    const dropdown = document.getElementById('notif-dropdown');
    if (!dropdown) return;
    dropdown.classList.toggle('active');
    if (dropdown.classList.contains('active')) {
        loadNotifications();
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const bell = document.getElementById('notif-bell');
    const dropdown = document.getElementById('notif-dropdown');
    if (bell && dropdown && !bell.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

async function loadNotifications() {
    const res = await apiGet('/api/notifications?limit=10');
    if (!res.success) return;

    const list = document.getElementById('notif-list');
    if (!list) return;

    if (res.data.notifications.length === 0) {
        list.innerHTML = '<div class="empty-state" style="padding:24px"><p class="text-secondary" style="font-size:0.8125rem">No notifications yet</p></div>';
        return;
    }

    list.innerHTML = res.data.notifications.map(n => {
        const dotColor = {
            hold_accepted: 'var(--green)',
            hold_rejected: 'var(--red)',
            hold_expired: 'var(--yellow)',
            room_taken: 'var(--red)',
            new_hold_request: 'var(--accent)',
            expiring_soon: 'var(--yellow)'
        }[n.notif_type] || 'var(--accent)';

        return `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markNotifRead(${n.id})">
                <div class="notif-dot" style="background:${dotColor}"></div>
                <div class="notif-content">
                    <div class="notif-title">${n.title}</div>
                    <div class="notif-text">${n.message}</div>
                    <div class="notif-time">${timeAgo(n.created_at)}</div>
                </div>
            </div>
        `;
    }).join('');

    // Update badge
    const badge = document.getElementById('bell-badge');
    if (badge) {
        if (res.data.unread_count > 0) {
            badge.textContent = res.data.unread_count > 9 ? '9+' : res.data.unread_count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

async function markNotifRead(id) {
    await apiPost('/api/notifications/read', { notification_id: id });
    loadNotifications();
}

async function markAllRead(e) {
    e.stopPropagation();
    await apiPost('/api/notifications/read');
    loadNotifications();
}

function updateBellBadge() {
    apiGet('/api/notifications?limit=1').then(res => {
        if (!res.success) return;
        const badge = document.getElementById('bell-badge');
        if (badge) {
            if (res.data.unread_count > 0) {
                badge.textContent = res.data.unread_count > 9 ? '9+' : res.data.unread_count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    });
}

function addNotificationToDropdown(data) {
    // If dropdown is open, prepend
    const list = document.getElementById('notif-list');
    if (list && document.getElementById('notif-dropdown')?.classList.contains('active')) {
        loadNotifications();
    }
}

// Check notifications periodically
setInterval(updateBellBadge, 60000);

// Initial load
if (typeof appState !== 'undefined' && appState.user && appState.user.id) {
    setTimeout(updateBellBadge, 1000);
}
