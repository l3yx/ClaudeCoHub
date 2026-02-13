document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('error');
    errEl.hidden = true;

    const uid = document.getElementById('uid').value.trim();
    const password = document.getElementById('password').value;

    try {
        const data = await apiFetch('/api/login', {
            method: 'POST',
            body: { uid, password },
        });
        setToken(data.token);
        localStorage.setItem('uid', data.uid);
        localStorage.setItem('username', data.username);
        window.location.href = '/dashboard.html';
    } catch (err) {
        errEl.textContent = err.message;
        errEl.hidden = false;
    }
});

// If already logged in, redirect
if (getToken()) {
    window.location.href = '/dashboard.html';
}
