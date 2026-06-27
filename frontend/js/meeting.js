async function genereazaMeeting() {
    const subject = document.getElementById('meeting-subject').value.trim() || 'BacInfo';
    const outputElement = document.getElementById('meeting-output');
    outputElement.textContent = 'Se generează linkul...';

    try {
        const response = await fetch(`${window.location.origin}/generate-meeting`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nume_materie: subject })
        });

        const result = await response.json();
        if (!response.ok) {
            outputElement.textContent = `Eroare server: ${result.detail || JSON.stringify(result)}`;
            return;
        }

        outputElement.innerHTML = `<strong>Link întâlnire:</strong> <a href="${result.link_intalnire}" target="_blank" rel="noreferrer">${result.link_intalnire}</a>`;
    } catch (error) {
        outputElement.textContent = 'Eroare la generare: ' + error.message;
    }
}
