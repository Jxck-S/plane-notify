let ws;
const wsUrl = (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws";

function connect() {
    ws = new WebSocket(wsUrl);

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const statusLine = document.getElementById('action-status');
        const btn = document.getElementById('reload-btn');
        const resultContainer = document.getElementById('result-container');

        if (data.type === 'status') {
            statusLine.textContent = data.message;
            statusLine.style.color = '#555'; // Reset color

            btn.disabled = true;
            btn.textContent = 'Processing...';
        } else if (data.type === 'result') {
            const stats = data.data;
            resultContainer.innerHTML = `
                <div class="result-summary">
                    <div>
                        <span class="badge badge-modified">Modified: ${stats.modified}</span>
                        <span class="badge badge-added">Added: ${stats.added}</span>
                        <span class="badge badge-removed">Removed: ${stats.removed}</span>
                        <span class="badge badge-unchanged">Unchanged: ${stats.unchanged}</span>
                        <span class="badge badge-unchanged" style="background-color: #17a2b8;">Total: ${stats.total}</span>
                    </div>
                </div>
                `;

            // If no changes, the "Reload complete" message from backend might be suppressed or different.
            // We can rely on the last message or just set a standard one.
            // But the backend sends a "Configuration unchanged" status message before the result msg usually.
            // Actually, let's just use a clear success message here.

            if (stats.modified === 0 && stats.added === 0 && stats.removed === 0) {
                statusLine.textContent = `Done. No changes found.`;
                statusLine.style.color = 'green';
            } else {
                statusLine.textContent = `Reload Complete. ${stats.total} planes active.`;
                statusLine.style.color = 'green';
            }
            statusLine.style.fontWeight = 'bold';

            btn.disabled = false;
            btn.textContent = 'Reload Config';

            // Refresh stats
            pollHeartbeat();
        } else if (data.type === 'error') {
            statusLine.textContent = "Error: " + data.message;
            statusLine.style.color = '#dc3545';
            statusLine.style.fontWeight = 'bold';

            btn.disabled = false;
            btn.textContent = 'Reload Config';
        }
    };

    ws.onclose = function (e) {
        console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
        setTimeout(function () {
            connect();
        }, 1000);
    };

    ws.onerror = function (err) {
        console.error('Socket encountered error: ', err.message, 'Closing socket');
        ws.close();
    };
}

function requestReload() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Clear log on new request
        document.getElementById('action-status').textContent = 'Requesting reload...';
        document.getElementById('result-container').innerHTML = '';
        ws.send(JSON.stringify({ action: "reload" }));
    } else {
        alert("WebSocket not connected. Please wait.");
    }
}

// Staleness tracking
let lastSuccessTime = 0;

function updateStatus(text, className) {
    const statusSpan = document.getElementById('hb-status');
    if (statusSpan) {
        statusSpan.textContent = text;
        statusSpan.className = className;
    }
}

function formatUptime(seconds) {
    seconds = Math.floor(seconds);
    const w = Math.floor(seconds / (3600 * 24 * 7));
    seconds -= w * 3600 * 24 * 7;
    const d = Math.floor(seconds / (3600 * 24));
    seconds -= d * 3600 * 24;
    const h = Math.floor(seconds / 3600);
    seconds -= h * 3600;
    const m = Math.floor(seconds / 60);
    seconds -= m * 60;
    const s = seconds;

    const parts = [];
    if (w > 0) parts.push(`${w}w`);
    if (d > 0) parts.push(`${d}d`);
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    parts.push(`${s}s`);

    return parts.join(' ');
}

function pollHeartbeat() {
    fetch('/heartbeat')
        .then(response => {
            if (!response.ok) throw new Error(`Server Error (${response.status})`);
            return response.json();
        })
        .then(data => {
            lastSuccessTime = Date.now();
            const uptimeSpan = document.getElementById('uptime');
            const countSpan = document.getElementById('plane-count');

            updateStatus('System Online', 'status-ok');
            uptimeSpan.textContent = formatUptime(data.uptime);
            if (data.plane_count !== undefined && countSpan) {
                countSpan.textContent = data.plane_count;
            }
        })
        .catch(error => {
            console.error("Heartbeat failed:", error);
            updateStatus('Backend Unreachable', 'status-error');
        });
}

function checkStaleness() {
    const now = Date.now();
    if (lastSuccessTime > 0 && (now - lastSuccessTime > 5000)) {
        const secondsAgo = Math.floor((now - lastSuccessTime) / 1000);
        const statusSpan = document.getElementById('hb-status');
        if (statusSpan && !statusSpan.classList.contains('status-error')) {
            updateStatus(`Connection Stale (Last seen ${secondsAgo}s ago)`, 'status-warning');
        }
    }
}

window.onload = function () {
    connect();
    setInterval(pollHeartbeat, 2000);
    setInterval(checkStaleness, 1000);
    pollHeartbeat();
};
