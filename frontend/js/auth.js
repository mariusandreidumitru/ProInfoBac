async function loginUser() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        alert('Te rog completează toate câmpurile!');
        return;
    }

    try {
        const response = await fetch(`${window.location.origin}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Autentificare eșuată.');
        }

        window.location.href = '/dashboard';
    } catch (error) {
        alert('Eroare la logare: ' + error.message);
    }
}

async function registerUser() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const role = document.getElementById('role') ? document.getElementById('role').value : 'student';

    if (!email || !password) {
        alert('Te rog completează toate câmpurile!');
        return;
    }

    try {
        const response = await fetch(`${window.location.origin}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, role })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Înregistrare eșuată.');
        }

        alert('Cont creat cu succes! Te poți autentifica acum.');
        window.location.href = '/';
    } catch (error) {
        alert('Eroare la înregistrare: ' + error.message);
    }
}
