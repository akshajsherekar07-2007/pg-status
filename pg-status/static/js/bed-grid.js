/**
 * StaySync — Bed Grid
 * Live DOM updates for bed tiles via Socket.IO events
 */

function updateBedTile(bedId, newStatus, data) {
    const tile = document.getElementById('bed-tile-' + bedId);
    if (!tile) return;

    const oldStatus = tile.dataset.status;
    tile.dataset.status = newStatus;

    // Remove old class, add new
    tile.classList.remove('bed-green', 'bed-yellow', 'bed-red');
    tile.classList.add('bed-' + newStatus);

    // Update icon
    const iconEl = tile.querySelector('.bed-tile-icon');
    if (iconEl) {
        if (newStatus === 'green') iconEl.innerHTML = '<i data-lucide="bed" style="width: 24px; height: 24px; display: inline-block;"></i>';
        else if (newStatus === 'yellow') iconEl.innerHTML = '<i data-lucide="clock" style="width: 24px; height: 24px; display: inline-block;"></i>';
        else iconEl.innerHTML = '<i data-lucide="lock" style="width: 24px; height: 24px; display: inline-block;"></i>';
    }

    // Update status text
    const statusEl = tile.querySelector('.bed-tile-status');
    if (statusEl) {
        if (newStatus === 'green') statusEl.textContent = 'Vacant';
        else if (newStatus === 'yellow') statusEl.textContent = 'On Hold';
        else statusEl.textContent = 'Occupied';
    }

    // Update countdown for yellow
    const countdownEl = tile.querySelector('.countdown');
    if (newStatus === 'yellow' && data && data.hold_expires_at) {
        if (countdownEl) {
            countdownEl.dataset.countdown = data.hold_expires_at;
            countdownEl.textContent = formatCountdown(data.hold_expires_at);
        } else {
            const cdDiv = document.createElement('div');
            cdDiv.className = 'countdown';
            cdDiv.dataset.countdown = data.hold_expires_at;
            cdDiv.textContent = formatCountdown(data.hold_expires_at);
            tile.insertBefore(cdDiv, tile.querySelector('.bed-tile-action'));
        }
    } else if (countdownEl && newStatus !== 'yellow') {
        countdownEl.remove();
    }

    // Update action button for student view
    const actionEl = tile.querySelector('.bed-tile-action');
    if (actionEl && appState && appState.user.role === 'student') {
        if (newStatus === 'green') {
            actionEl.innerHTML = `<button class="btn btn-green btn-sm" onclick="openHoldModal(${bedId}, '${data?.bed_label || ''}', '${data?.room_number || ''}', '', 0)">Hold This</button>`;
            actionEl.style.display = '';
        } else {
            actionEl.style.display = 'none';
        }
    }

    // Update info for red beds
    const infoEl = tile.querySelector('.bed-tile-info');
    if (newStatus === 'red' && !infoEl) {
        const info = document.createElement('div');
        info.className = 'bed-tile-info';
        info.textContent = 'Since ' + new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        tile.appendChild(info);
    } else if (newStatus !== 'red' && infoEl) {
        infoEl.remove();
    }

    // Animation on change
    tile.style.transform = 'scale(1.05)';
    setTimeout(() => { tile.style.transform = ''; }, 300);

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Update appState
    if (typeof appState !== 'undefined') {
        appState.beds[bedId] = { status: newStatus, ...data };
    }

    console.log(`Bed ${bedId} updated: ${oldStatus} → ${newStatus}`);
}

function updateAvailabilityPills(propertyId) {
    // Refresh pills on property cards (browse page)
    const pillsContainer = document.querySelector(`[data-property-pills="${propertyId}"]`);
    if (!pillsContainer) return;

    // Fetch updated counts
    apiGet(`/api/beds/${propertyId}/status`).then(res => {
        if (!res.success) return;
        let green = 0, yellow = 0, red = 0;
        res.data.forEach(bed => {
            if (bed.status === 'green') green++;
            else if (bed.status === 'yellow') yellow++;
            else red++;
        });
        const pills = pillsContainer.querySelectorAll('.availability-pill .count');
        if (pills[0]) pills[0].textContent = green;
        if (pills[1]) pills[1].textContent = yellow;
        if (pills[2]) pills[2].textContent = red;
    });
}
