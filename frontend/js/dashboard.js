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

async function genereazaTest() {
    const category = document.getElementById('test-category').value.trim();
    const count = Number(document.getElementById('test-count').value) || 5;
    const minDifficulty = Number(document.getElementById('test-min-difficulty').value) || 1;
    const maxDifficulty = Number(document.getElementById('test-max-difficulty').value) || 10;
    const outputElement = document.getElementById('test-output');

    outputElement.textContent = 'Se generează testul...';

    try {
        const response = await fetch(`${window.location.origin}/generate-test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, count, min_difficulty: minDifficulty, max_difficulty: maxDifficulty })
        });

        const result = await response.json();
        if (!response.ok) {
            outputElement.textContent = `Eroare server: ${result.detail || JSON.stringify(result)}`;
            return;
        }

        const questions = result.questions || [];
        if (!questions.length) {
            outputElement.textContent = 'Nu s-au generat întrebări. Încearcă alte criterii.';
            return;
        }

        const lines = questions.map((item, index) => {
            return `${index + 1}. [Dificultate ${item.difficulty}] ${item.question}`;
        });

        outputElement.textContent = lines.join('\n\n');
    } catch (error) {
        outputElement.textContent = 'Eroare la generare: ' + error.message;
    }
}
