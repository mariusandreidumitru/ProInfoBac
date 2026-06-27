async function ruleazaCod() {
    const code = document.getElementById('code-editor').value;
    const stdin = document.getElementById('stdin-input').value;
    const outputElement = document.getElementById('output');

    outputElement.textContent = 'Se rulează codul...';

    try {
        const response = await fetch(`${window.location.origin}/compile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language: 'cpp', stdin })
        });

        const result = await response.json();
        if (!response.ok) {
            outputElement.textContent = `Eroare server: ${result.detail || JSON.stringify(result)}`;
            return;
        }

        let text = `Exit code: ${result.exit_code}\n`;
        if (result.output) {
            text += `\nOutput:\n${result.output}`;
        }
        if (result.error) {
            text += `\nEroare:\n${result.error}`;
        }
        outputElement.textContent = text.trim();
    } catch (error) {
        outputElement.textContent = 'Eroare la rulare: ' + error.message;
    }
}
