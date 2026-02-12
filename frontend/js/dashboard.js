if (!requireAuth()) throw new Error('Not authenticated');

document.getElementById('userDisplay').textContent = localStorage.getItem('username') || '';

function logout() {
    clearToken();
    window.location.href = '/index.html';
}

async function loadSessions() {
    try {
        const sessions = await apiFetch('/api/sessions');
        const tbody = document.getElementById('sessionsBody');
        if (sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">No sessions yet</td></tr>';
            return;
        }
        tbody.innerHTML = sessions.map(s => `
            <tr>
                <td><code>${s.session_id.substring(0, 8)}</code></td>
                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${s.first_message || ''}">${s.first_message || '-'}</td>
                <td>${s.updated_at ? new Date(s.updated_at).toLocaleString() : '-'}</td>
                <td><span class="badge badge-${s.status}">${s.status}</span></td>
                <td class="actions">
                    ${s.alive
                        ? `<a class="btn" href="/terminal.html?session=${s.session_id}">Open</a>
                           <button class="btn btn-danger" onclick="closeSession('${s.session_id}')">Close</button>`
                        : `<button class="btn btn-success" onclick="resumeSession('${s.session_id}')">Resume</button>
                           <button class="btn btn-danger" onclick="deleteSession('${s.session_id}')">Delete</button>`
                    }
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
}

async function createSession() {
    try {
        const data = await apiFetch('/api/sessions', { method: 'POST' });
        window.location.href = `/terminal.html?session=${data.session_id}`;
    } catch (err) {
        alert('Failed to create session: ' + err.message);
    }
}

async function resumeSession(id) {
    try {
        await apiFetch(`/api/sessions/${id}/resume`, { method: 'POST' });
        window.location.href = `/terminal.html?session=${id}`;
    } catch (err) {
        alert('Failed to resume: ' + err.message);
    }
}

async function closeSession(id) {
    if (!confirm('Close this session?')) return;
    try {
        await apiFetch(`/api/sessions/${id}`, { method: 'DELETE' });
        loadSessions();
    } catch (err) {
        alert('Failed to close: ' + err.message);
    }
}

async function deleteSession(id) {
    if (!confirm('Delete this session permanently?')) return;
    try {
        await apiFetch(`/api/sessions/${id}/delete`, { method: 'DELETE' });
        loadSessions();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

loadSessions();
setInterval(loadSessions, 5000);
