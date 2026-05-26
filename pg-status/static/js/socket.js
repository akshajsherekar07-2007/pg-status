/**
 * StaySync — Socket.IO Client
 * Auto-reconnect with exponential backoff, room management, event handling
 */

let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000;

function initSocket() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded, using polling fallback');
        startPollingFallback();
        return;
    }

    socket = io({
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: MAX_RECONNECT_DELAY,
        reconnectionAttempts: Infinity
    });

    socket.on('connect', () => {
        console.log('Socket connected:', socket.id);
        reconnectAttempts = 0;

        // Re-join property room if on property page
        const bedGrid = document.getElementById('bed-grid-container');
        if (bedGrid) {
            const propertyId = bedGrid.dataset.propertyId;
            if (propertyId) socket.emit('join_property', { property_id: parseInt(propertyId) });
        }
    });

    socket.on('disconnect', () => {
        console.warn('Socket disconnected');
    });

    socket.on('connect_error', (err) => {
        reconnectAttempts++;
        console.warn(`Socket reconnect attempt ${reconnectAttempts}`);
        if (reconnectAttempts > 10) {
            console.warn('Falling back to polling');
            startPollingFallback();
        }
    });

    // ---- EVENT HANDLERS ----

    socket.on('bed_status_changed', (data) => {
        console.log('Bed status changed:', data);
        updateBedTile(data.bed_id, data.new_status, data);
        updateAvailabilityPills(data.property_id);
    });

    socket.on('hold_accepted', (data) => {
        showToast('success', 'Hold Accepted! 🎉', `Your hold on ${data.bed_label} at ${data.property_name} has been accepted.`);
        if (typeof updateDashboard === 'function') updateDashboard();
    });

    socket.on('hold_rejected', (data) => {
        showToast('error', 'Hold Rejected', `Your hold on ${data.bed_label} at ${data.property_name} was rejected. Reason: ${data.reason || 'Not specified'}`);
    });

    socket.on('room_taken_hold_override', (data) => {
        showUrgentModal(data);
    });

    socket.on('hold_expired', (data) => {
        showToast('warning', 'Hold Expired', `Your hold at ${data.property_name} has expired. Score change: ${data.score_change}`);
        if (typeof updateDashboard === 'function') updateDashboard();
    });

    socket.on('hold_expiring_soon', (data) => {
        showToast('warning', 'Hold Expiring Soon ⚠️', `Your hold at ${data.property_name} expires in ${data.hours_remaining} hours.`);
    });

    socket.on('new_hold_request', (data) => {
        showToast('info', 'New Hold Request', `${data.student_name} (Score: ${data.student_score}) wants a ${data.hold_days}-day hold on ${data.bed_label}`);
        updateBellBadge();
    });

    socket.on('notification', (data) => {
        updateBellBadge();
        addNotificationToDropdown(data);
    });
}

function showUrgentModal(data) {
    const overlay = document.getElementById('urgent-modal-overlay');
    const body = document.getElementById('urgent-modal-body');
    if (!overlay || !body) return;

    body.innerHTML = `
        <div style="text-align:center;padding:20px 0">
            <div style="font-size:4rem;margin-bottom:16px;animation:pulse 1.5s ease-in-out infinite">🔴</div>
            <h2 style="color:var(--red);margin-bottom:12px">Room Taken</h2>
            <p style="color:var(--text-secondary);margin-bottom:8px">A walk-in student took <strong>${data.bed_label}</strong> at <strong>${data.property_name}</strong>.</p>
            <p style="font-size:0.875rem;color:var(--text-muted);margin-bottom:24px">Your reliability score is NOT affected.</p>
            <a href="/student/browse" class="btn btn-primary btn-lg">Find Similar Properties →</a>
            <button class="btn btn-ghost" style="margin-top:12px;display:block;width:100%" onclick="document.getElementById('urgent-modal-overlay').classList.remove('active')">Dismiss</button>
        </div>
    `;
    overlay.classList.add('active');
}

function startPollingFallback() {
    const bedGrid = document.getElementById('bed-grid-container');
    if (!bedGrid) return;
    const propertyId = bedGrid.dataset.propertyId;
    if (!propertyId) return;

    setInterval(async () => {
        const res = await apiGet(`/api/beds/${propertyId}/status`);
        if (res.success && res.data) {
            res.data.forEach(bed => updateBedTile(bed.id, bed.status, bed));
        }
    }, 30000);
}

// Initialize on page load
if (typeof appState !== 'undefined' && appState.user && appState.user.id) {
    initSocket();
}
