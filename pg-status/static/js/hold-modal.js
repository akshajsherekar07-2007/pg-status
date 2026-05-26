/**
 * StaySync — Hold Modal Logic
 * 2-step hold request: duration selection → confirmation
 */

let holdModalState = {
    bedId: null,
    bedLabel: '',
    roomNumber: '',
    propertyName: '',
    rentPerBed: 0,
    holdDays: 3
};

function openHoldModal(bedId, bedLabel, roomNumber, propertyName, rentPerBed) {
    holdModalState = { bedId, bedLabel, roomNumber, propertyName, rentPerBed, holdDays: 3 };

    document.getElementById('hold-modal-subtitle').textContent =
        `${bedLabel} · Room ${roomNumber} · ${propertyName}`;

    selectDuration(3);
    showHoldStep1();
    document.getElementById('hold-modal-overlay').classList.add('active');
}

function closeHoldModal() {
    document.getElementById('hold-modal-overlay').classList.remove('active');
}

function selectDuration(days) {
    holdModalState.holdDays = days;
    document.querySelectorAll('#duration-chips .chip').forEach(c => {
        c.classList.remove('active');
        if (c.textContent.trim().startsWith(days.toString())) {
            c.classList.add('active');
        }
    });

    const expiry = new Date();
    expiry.setDate(expiry.getDate() + days);
    document.getElementById('hold-expiry-preview').textContent =
        `Expires on ${expiry.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}`;
}

function showHoldStep1() {
    document.getElementById('hold-step-1').style.display = 'block';
    document.getElementById('hold-step-2').style.display = 'none';
}

function showHoldStep2() {
    document.getElementById('hold-step-1').style.display = 'none';
    document.getElementById('hold-step-2').style.display = 'block';

    const expiry = new Date();
    expiry.setDate(expiry.getDate() + holdModalState.holdDays);

    document.getElementById('hold-summary').innerHTML = `
        <div style="display:flex;flex-direction:column;gap:8px">
            <div style="display:flex;justify-content:space-between"><span style="color:var(--text-muted)">Property</span><span>${holdModalState.propertyName}</span></div>
            <div style="display:flex;justify-content:space-between"><span style="color:var(--text-muted)">Bed</span><span>${holdModalState.bedLabel} · Room ${holdModalState.roomNumber}</span></div>
            <div style="display:flex;justify-content:space-between"><span style="color:var(--text-muted)">Duration</span><span>${holdModalState.holdDays} days</span></div>
            <div style="display:flex;justify-content:space-between"><span style="color:var(--text-muted)">Expires</span><span>${expiry.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span></div>
            ${holdModalState.rentPerBed ? `<div style="display:flex;justify-content:space-between"><span style="color:var(--text-muted)">Rent</span><span>₹${Number(holdModalState.rentPerBed).toLocaleString('en-IN')}/month</span></div>` : ''}
        </div>
    `;

    // Reset checkbox
    document.getElementById('hold-confirm-check').checked = false;
    document.getElementById('submit-hold-btn').disabled = true;

    document.getElementById('hold-confirm-check').onchange = function () {
        document.getElementById('submit-hold-btn').disabled = !this.checked;
    };
}

async function submitHoldRequest() {
    const btn = document.getElementById('submit-hold-btn');
    btn.disabled = true;
    btn.textContent = 'Submitting...';

    const res = await apiPost('/api/holds/request', {
        bed_id: holdModalState.bedId,
        hold_days: holdModalState.holdDays
    });

    if (res.success) {
        closeHoldModal();
        showToast('success', 'Hold Requested! 🎉', 'Your hold request has been sent to the owner.');

        // Update bed tile to show pending state
        const tile = document.getElementById('bed-tile-' + holdModalState.bedId);
        if (tile) {
            const action = tile.querySelector('.bed-tile-action');
            if (action) {
                action.innerHTML = '<span class="badge badge-accent" style="font-size:0.6875rem">Hold Requested</span>';
            }
        }
    } else {
        showToast('error', 'Request Failed', res.error || 'Could not place hold. Please try again.');
        btn.disabled = false;
        btn.textContent = 'Submit Hold Request';
    }
}
