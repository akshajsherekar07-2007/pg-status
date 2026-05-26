/**
 * StaySync — Countdown Timer
 * Live countdown that updates every second
 */

function updateCountdowns() {
    document.querySelectorAll('[data-countdown]').forEach(el => {
        const target = el.dataset.countdown;
        if (!target) return;

        const now = new Date();
        const expiry = new Date(target);
        const diff = expiry - now;

        if (diff <= 0) {
            el.textContent = 'Expired';
            el.style.color = 'var(--red)';
            return;
        }

        const days = Math.floor(diff / 86400000);
        const hours = Math.floor((diff % 86400000) / 3600000);
        const mins = Math.floor((diff % 3600000) / 60000);
        const secs = Math.floor((diff % 60000) / 1000);

        if (days > 0) {
            el.textContent = `${days}d ${hours}h ${mins}m`;
        } else if (hours > 0) {
            el.textContent = `${hours}h ${mins}m ${secs}s`;
        } else {
            el.textContent = `${mins}m ${secs}s`;
            if (diff < 3600000) el.style.color = 'var(--red)';
        }

        // Prefix icon for bed tiles
        if (el.classList.contains('countdown')) {
            el.textContent = '⏱ ' + el.textContent;
        }
    });
}

// Update every second
setInterval(updateCountdowns, 1000);
// Initial update
updateCountdowns();
