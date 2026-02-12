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
                <td><code>${s.id}</code></td>
                <td>${s.description}</td>
                <td><code>${s.cron}</code></td>
                <td>
                    <button class="btn ${s.enabled ? 'btn-success' : ''}" onclick="toggleSchedule('${s.id}', ${!s.enabled})">
                        ${s.enabled ? 'On' : 'Off'}
                    </button>
                </td>
                <td class="actions">
                    <button class="btn btn-danger" onclick="deleteSchedule('${s.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load schedules:', err);
    }
}

async function addSchedule() {
    const description = document.getElementById('schedDesc').value.trim();
    const cron = document.getElementById('schedCron').value.trim();
    if (!description || !cron) return alert('Fill in all fields');

    try {
        await apiFetch('/api/schedules', {
            method: 'POST',
            body: { description, cron },
        });
        document.getElementById('schedDesc').value = '';
        document.getElementById('schedCron').value = '';
        loadSchedules();
    } catch (err) {
        alert('Failed to add schedule: ' + err.message);
    }
}

async function toggleSchedule(id, enabled) {
    try {
        await apiFetch(`/api/schedules/${id}`, {
            method: 'PUT',
            body: { enabled },
        });
        loadSchedules();
    } catch (err) {
        alert('Failed to update: ' + err.message);
    }
}

async function deleteSchedule(id) {
    if (!confirm('Delete this schedule?')) return;
    try {
        await apiFetch(`/api/schedules/${id}`, { method: 'DELETE' });
        loadSchedules();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

loadSchedules();
