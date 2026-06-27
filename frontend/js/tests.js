let lastGeneratedQuestions = [];
let currentQuestion = null;
let currentQuestionIndex = -1;
let codeRunAttempts = 0;
let lastScore = 0;
const MAX_ATTEMPTS_BEFORE_SOLUTION = 3;
const SCORE_THRESHOLD = 70;

async function genereazaTest() {
    const category = document.getElementById('test-category').value.trim();
    const count = Number(document.getElementById('test-count').value) || 5;
    const minDifficulty = Number(document.getElementById('test-min-difficulty').value) || 1;
    const maxDifficulty = Number(document.getElementById('test-max-difficulty').value) || 10;
    const role = document.getElementById('test-role').value;
    const types = Array.from(document.querySelectorAll('input[name="test-type"]:checked')).map(el => el.value);
    const outputElement = document.getElementById('test-output');

    outputElement.textContent = 'Se generează testul...';

    try {
        const response = await fetch(`${window.location.origin}/generate-test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, count, min_difficulty: minDifficulty, max_difficulty: maxDifficulty, role, exercise_types: types })
        });

        const result = await response.json();
        if (!response.ok) {
            outputElement.textContent = `Eroare server: ${result.detail || JSON.stringify(result)}`;
            return;
        }

        const questions = result.questions || [];
        if (!questions.length) {
            outputElement.textContent = 'Nu s-au generat întrebări. Încearcă alte criterii.';
            document.getElementById('test-questions-list').textContent = 'Nu există întrebări generate.';
            return;
        }

        lastGeneratedQuestions = questions;
        currentQuestionIndex = -1;
        lastScore = 0;
        renderTestQuestions(questions);
        loadFirstQuestion();
    } catch (error) {
        outputElement.textContent = 'Eroare la generare: ' + error.message;
    }
}

function renderQuestionList(questions) {
    const listContainer = document.getElementById('test-questions-list');
    if (!listContainer) return;
    const items = questions.map((item, index) => {
        return `${index + 1}. [${item.exercise_type.toUpperCase()}] ${item.question}`;
    });
    listContainer.textContent = items.join('\n\n');
}

function renderTestQuestions(questions) {
    renderQuestionList(questions);
    const outputElement = document.getElementById('test-output');
    if (outputElement) {
        outputElement.textContent = `Test generat: ${questions.length} întrebări. Prima întrebare s-a încărcat automat.`;
    }
}

function updateCodeScoreDisplay(score) {
    const scoreContainer = document.getElementById('code-score');
    if (!scoreContainer) return;
    scoreContainer.textContent = `Punctaj curent: ${score} / 100`;
}

function updateQuestionTypeLabel(type) {
    const typeContainer = document.getElementById('question-type');
    if (!typeContainer) return;
    typeContainer.textContent = `Tip exercițiu: ${type.toUpperCase()}`;
}

function showFeedback(message) {
    const feedback = document.getElementById('solution-feedback');
    if (feedback) {
        feedback.textContent = message;
    }
}

function resetAnswerSections() {
    const codeSection = document.getElementById('code-answer-section');
    const grilaSection = document.getElementById('grila-answer-section');
    const writtenSection = document.getElementById('written-answer-section');
    if (codeSection) codeSection.style.display = 'none';
    if (grilaSection) grilaSection.style.display = 'none';
    if (writtenSection) writtenSection.style.display = 'none';
}

function setActiveQuestion(question, index) {
    const promptContainer = document.getElementById('code-question-prompt');
    const hintContainer = document.getElementById('code-hint');
    const solutionContainer = document.getElementById('code-solution');
    if (!promptContainer || !hintContainer || !solutionContainer) return;

    currentQuestion = question;
    currentQuestionIndex = index;
    codeRunAttempts = 0;
    lastScore = 0;
    promptContainer.textContent = question.question;
    hintContainer.textContent = question.hint || 'Acest exercițiu nu are hint disponibil.';
    solutionContainer.textContent = 'Soluția completă este dezactivată până la câteva încercări nereușite.';
    updateCodeScoreDisplay(lastScore);
    updateQuestionTypeLabel(question.exercise_type);
    resetAnswerSections();
    showFeedback('');

    const type = (question.exercise_type || '').toLowerCase();
    if (type === 'cod') {
        const codeSection = document.getElementById('code-answer-section');
        const editor = document.getElementById('test-code-editor');
        if (codeSection && editor) {
            codeSection.style.display = 'block';
            editor.value = '';
        }
    } else if (type === 'grila') {
        const grilaSection = document.getElementById('grila-answer-section');
        const codeSection = document.getElementById('code-answer-section');
        if (codeSection) codeSection.style.display = 'none';
        if (grilaSection) {
            grilaSection.style.display = 'block';
            renderGrilaOptions(question.options || []);
        }
    } else if (type === 'scris') {
        const codeSection = document.getElementById('code-answer-section');
        const writtenSection = document.getElementById('written-answer-section');
        const writtenInput = document.getElementById('test-written-answer');
        if (codeSection) codeSection.style.display = 'none';
        if (writtenSection && writtenInput) {
            writtenSection.style.display = 'block';
            writtenInput.value = '';
        }
    }
}

function renderGrilaOptions(options) {
    const optionsContainer = document.getElementById('grila-options');
    if (!optionsContainer) return;
    if (!options || !options.length) {
        optionsContainer.textContent = 'Nu există opțiuni disponibile.';
        return;
    }
    optionsContainer.innerHTML = options.map((option, index) => {
        return `<label><input type="radio" name="grila-answer" value="${option}"> ${option}</label>`;
    }).join('<br>');
}

function loadFirstQuestion() {
    if (!lastGeneratedQuestions.length) {
        showFeedback('Generează un test pentru a începe.');
        return;
    }
    const firstCodQuestion = lastGeneratedQuestions.find(q => q.exercise_type === 'cod');
    if (firstCodQuestion) {
        const index = lastGeneratedQuestions.indexOf(firstCodQuestion);
        setActiveQuestion(firstCodQuestion, index);
        return;
    }
    setActiveQuestion(lastGeneratedQuestions[0], 0);
}

function loadNextQuestion() {
    if (!lastGeneratedQuestions.length) {
        showFeedback('Nu există întrebări disponibile.');
        return false;
    }
    const nextIndex = currentQuestionIndex + 1;
    if (nextIndex >= lastGeneratedQuestions.length) {
        showFeedback('Ai terminat toate întrebările din test.');
        currentQuestion = null;
        updateQuestionTypeLabel('Niciunul');
        return false;
    }
    setActiveQuestion(lastGeneratedQuestions[nextIndex], nextIndex);
    return true;
}

async function submitSolution() {
    const outputElement = document.getElementById('question-result');
    if (!currentQuestion) {
        showFeedback('Nu există un exercițiu activ. Generează un test mai întâi.');
        return;
    }

    if (currentQuestion.exercise_type === 'cod') {
        const code = document.getElementById('test-code-editor').value;
        if (!code.trim()) {
            showFeedback('Scrie soluția în editor înainte să trimiți.');
            return;
        }
        outputElement.textContent = 'Se verifică soluția C++...';
        await evaluateCodeSubmission(code, outputElement, true);
    } else if (currentQuestion.exercise_type === 'grila') {
        const selected = document.querySelector('input[name="grila-answer"]:checked');
        if (!selected) {
            showFeedback('Alege o variantă înainte să trimiți.');
            return;
        }
        evaluateGrilaSubmission(selected.value, outputElement);
    } else if (currentQuestion.exercise_type === 'scris') {
        const answer = document.getElementById('test-written-answer').value;
        if (!answer.trim()) {
            showFeedback('Scrie un răspuns înainte să trimiți.');
            return;
        }
        evaluateWrittenSubmission(answer, outputElement);
    }
}

function runCurrentCode() {
    if (!currentQuestion || currentQuestion.exercise_type !== 'cod') {
        showFeedback('Nu există un exercițiu cod activ sau nu este un exercițiu cod.');
        return;
    }
    const code = document.getElementById('test-code-editor').value;
    const outputElement = document.getElementById('question-result');
    if (!code.trim()) {
        showFeedback('Scrie codul în editor înainte să rulezi.');
        return;
    }
    outputElement.textContent = 'Se rulează codul...';
    evaluateCodeSubmission(code, outputElement, false);
}

async function evaluateCodeSubmission(code, outputElement, advanceOnSuccess = false) {
    try {
        const response = await fetch(`${window.location.origin}/compile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language: 'cpp' })
        });

        const result = await response.json();
        if (!response.ok) {
            outputElement.textContent = `Eroare server: ${result.detail || JSON.stringify(result)}`;
            return;
        }

        let text = `Exit code: ${result.exit_code}`;
        if (result.output) {
            text += `\nOutput:\n${result.output}`;
        }
        if (result.error) {
            text += `\nEroare:\n${result.error}`;
        }
        outputElement.textContent = text;
        const success = result.exit_code === 0 && !result.error;
        lastScore = success ? 100 : 0;
        updateCodeScoreDisplay(lastScore);
        if (success) {
            showFeedback('Soluția este corectă.');
            if (advanceOnSuccess) {
                showFeedback('Soluția este corectă. Se trece la următorul exercițiu.');
                const advanced = loadNextQuestion();
                if (advanced) {
                    outputElement.textContent += '\n\nUrmătorul exercițiu a fost încărcat.';
                }
            }
        } else {
            codeRunAttempts += 1;
            if (codeRunAttempts > MAX_ATTEMPTS_BEFORE_SOLUTION && currentQuestion.solution_code) {
                document.getElementById('code-solution').textContent = currentQuestion.solution_code;
            }
            showFeedback('Soluția nu este încă corectă. Încearcă din nou.');
        }
    } catch (error) {
        outputElement.textContent = 'Eroare la rulare: ' + error.message;
        showFeedback('A apărut o eroare la verificarea codului.');
    }
}

function evaluateGrilaSubmission(answer, outputElement) {
    const normalizedAnswer = answer.trim();
    const expected = (currentQuestion.answer || '').trim();
    const success = normalizedAnswer === expected;
    lastScore = success ? 100 : 0;
    updateCodeScoreDisplay(lastScore);
    outputElement.textContent = success ? 'Răspuns corect.' : `Răspuns greșit. Varianta corectă este ${expected}.`;
    showFeedback(success ? 'Felicitări! Treci la următorul exercițiu.' : 'Încearcă să recitești întrebarea și să trimiți din nou.');
    if (success) {
        loadNextQuestion();
    }
}

function evaluateWrittenSubmission(answer, outputElement) {
    const normalizedAnswer = normalizeText(answer);
    const expected = normalizeText(currentQuestion.answer || '');
    const success = expected && normalizedAnswer === expected;
    lastScore = success ? 100 : 0;
    updateCodeScoreDisplay(lastScore);
    outputElement.textContent = success ? 'Răspuns corect.' : 'Răspuns greșit. Încearcă încă o dată sau cere hintul.';
    showFeedback(success ? 'Felicitări! Treci la următorul exercițiu.' : 'Încearcă din nou, folosește hintul și trimite alt răspuns.' );
    if (success) {
        loadNextQuestion();
    }
}

function normalizeText(text) {
    return text.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[^a-z0-9 ]/g, '');
}
