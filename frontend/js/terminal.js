if (!requireAuth()) throw new Error('Not authenticated');

const params = new URLSearchParams(location.search);
const sessionId = params.get('session');
if (!sessionId) {
    window.location.href = '/dashboard.html';
    throw new Error('No session ID');
}

document.getElementById('sessionLabel').textContent = sessionId.substring(0, 8);

const term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
        background: '#0d1117',
        foreground: '#e6edf3',
        cursor: '#58a6ff',
    },
});

const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminalContainer'));
fitAddon.fit();

let ws = null;

function connect() {
    const url = getWsUrl(`/api/ws/terminal/${sessionId}`);
    ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
        document.getElementById('overlay').style.display = 'none';
        ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
    };

    ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
            term.write(new Uint8Array(event.data));
        } else {
            term.write(event.data);
        }
    };

    ws.onclose = () => {
        document.getElementById('overlay').style.display = 'flex';
    };

    ws.onerror = () => {
        document.getElementById('overlay').style.display = 'flex';
    };
}

term.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(data);
    }
});

// Handle resize
window.addEventListener('resize', () => {
    fitAddon.fit();
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
    }
});

function reconnect() {
    if (ws) {
        ws.close();
    }
    connect();
}

connect();
