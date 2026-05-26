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

        // Reset classes
        el.classList.remove('timer-warning', 'timer-urgent');

        if (diff <= 0) {
            el.textContent = 'Expired';
            el.classList.add('timer-warning');
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
        }

        // Apply warning/urgent states based on time left
        if (diff < 3600000) { // Under 1 hour
            el.classList.add('timer-warning');
        }
        if (diff < 900000) { // Under 15 minutes
            el.classList.add('timer-urgent');
        }

        // Prefix icon for bed tiles
        if (el.classList.contains('countdown')) {
            const timeText = el.textContent;
            el.innerHTML = '<i data-lucide="clock" style="width: 12px; height: 12px; vertical-align: middle; margin-right: 4px; display: inline-block;"></i>' + timeText;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    });
}

// Update every second
setInterval(updateCountdowns, 1000);
// Initial update
updateCountdowns();
