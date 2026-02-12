async function loadSchedules() {
    try {
        const schedules = await apiFetch('/api/schedules');
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
                <td>
                    <button class="btn ${s.enabled ? 'btn-success' : ''}" onclick="toggleSchedule('${s.name}', ${!s.enabled})">
                        ${s.enabled ? 'On' : 'Off'}
                    </button>
                </td>
                <td class="actions">
                    <button class="btn btn-danger" onclick="deleteSchedule('${s.name}')">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load schedules:', err);
    }
}

async function addSchedule() {
    const name = document.getElementById('schedName').value.trim();
    const content = document.getElementById('schedContent').value.trim();
    const cron = document.getElementById('schedCron').value.trim();
    if (!name || !content || !cron) return alert('Fill in name, content and cron');

    try {
        await apiFetch('/api/schedules', {
            method: 'POST',
            body: { name, content, cron },
        });
        document.getElementById('schedName').value = '';
        document.getElementById('schedContent').value = '';
        document.getElementById('schedCron').value = '';
        loadSchedules();
    } catch (err) {
        alert('Failed to add schedule: ' + err.message);
    }
}

async function toggleSchedule(name, enabled) {
    try {
        await apiFetch(`/api/schedules/${name}`, {
            method: 'PUT',
            body: { enabled },
        });
        loadSchedules();
    } catch (err) {
        alert('Failed to update: ' + err.message);
    }
}

async function deleteSchedule(name) {
    if (!confirm('Delete this schedule?')) return;
    try {
        await apiFetch(`/api/schedules/${name}`, { method: 'DELETE' });
        loadSchedules();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

loadSchedules();
