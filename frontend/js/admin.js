if (!requireAuth()) throw new Error('Not authenticated');

document.getElementById('userDisplay').textContent = localStorage.getItem('username') || '';

function logout() {
    clearToken();
    window.location.href = '/index.html';
}

async function loadOverview() {
    try {
        const data = await apiFetch('/api/admin/overview');
        renderUsers(data.users);
        renderSchedules(data.schedules);
    } catch (err) {
        console.error('Failed to load overview:', err);
    }
}

function renderUsers(users) {
    const container = document.getElementById('usersContainer');
    if (users.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted)">No users found</p>';
        return;
    }
    container.innerHTML = users.map(u => `
        <h3 style="margin:1rem 0 0.5rem">${u.username} (${u.sessions.length})</h3>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Session ID</th>
                        <th>First Message</th>
                        <th>Updated</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${u.sessions.length === 0
                        ? '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No sessions</td></tr>'
                        : u.sessions.map(s => `
                            <tr>
                                <td><code>${s.session_id.substring(0, 8)}</code></td>
                                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${s.first_message || ''}">${s.first_message || '-'}</td>
                                <td>${s.updated_at ? new Date(s.updated_at).toLocaleString() : '-'}</td>
                                <td><span class="badge badge-${s.status}">${s.status}</span></td>
                            </tr>
                        `).join('')}
                </tbody>
            </table>
        </div>
    `).join('');
}

function renderSchedules(schedules) {
    const tbody = document.getElementById('schedulesBody');
    if (schedules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">No scheduled tasks</td></tr>';
        return;
    }
    tbody.innerHTML = schedules.map(s => `
        <tr>
            <td>${s.name}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${s.content}">${s.content}</td>
            <td><code>${s.cron}</code></td>
            <td>${s.workdir || '-'}</td>
            <td><span class="badge badge-${s.enabled ? 'idle' : 'dead'}">${s.enabled ? 'On' : 'Off'}</span></td>
        </tr>
    `).join('');
}

loadOverview();
setInterval(loadOverview, 5000);
