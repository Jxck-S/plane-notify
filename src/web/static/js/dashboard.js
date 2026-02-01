let ws;
const wsUrl = (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws";

function connect() {
    ws = new WebSocket(wsUrl);

    ws.addEventListener('message', function (event) {
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
            resultContainer.textContent = '';
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'result-summary';

            const innerDiv = document.createElement('div');

            const createBadge = (label, count, className, styles = {}) => {
                const span = document.createElement('span');
                span.className = `badge ${className}`;
                span.textContent = `${label}: ${count}`;
                for (const [key, value] of Object.entries(styles)) {
                    span.style[key] = value;
                }
                return span;
            };

            innerDiv.appendChild(createBadge('Modified', stats.modified, 'badge-modified'));
            innerDiv.appendChild(createBadge('Added', stats.added, 'badge-added'));
            innerDiv.appendChild(createBadge('Removed', stats.removed, 'badge-removed'));
            innerDiv.appendChild(createBadge('Unchanged', stats.unchanged, 'badge-unchanged'));
            innerDiv.appendChild(createBadge('Total', stats.total, 'badge-unchanged', { backgroundColor: '#17a2b8' }));

            summaryDiv.appendChild(innerDiv);
            resultContainer.appendChild(summaryDiv);

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
    });

    ws.addEventListener('close', function (e) {
        // Reconnect will be attempted
        setTimeout(function () {
            connect();
        }, 1000);
    });

    ws.addEventListener('error', function (err) {
        console.error('Socket encountered error: ', err.message, 'Closing socket');
        ws.close();
    });
}

function requestReload() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Clear log on new request
        document.getElementById('action-status').textContent = 'Requesting reload...';
        document.getElementById('result-container').innerHTML = '';
        ws.send(JSON.stringify({ action: "reload" }));
    } else {
        const statusLine = document.getElementById('action-status');
        if (statusLine) {
            statusLine.textContent = "WebSocket not connected. Please wait.";
            statusLine.style.color = '#dc3545';
        }
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

window.addEventListener('load', function () {
    connect();
    setInterval(pollHeartbeat, 2000);
    setInterval(checkStaleness, 1000);
    pollHeartbeat();
});
