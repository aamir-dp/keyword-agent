const API_URL = 'https://your-render-app.onrender.com'; // Replace with your Render URL

// DOM Elements
const generateBtn = document.getElementById('generateBtn');
const reportBtn = document.getElementById('reportBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');

// Event Listeners
generateBtn.addEventListener('click', () => handleRequest('/generate-keywords', displayKeywordResults));
reportBtn.addEventListener('click', () => handleRequest('/generate-report', displayReportResults));

document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabId = button.dataset.tab;
        showTab(tabId);
    });
});

async function handleRequest(endpoint, callback) {
    const category = document.getElementById('category').value;
    const platform = document.getElementById('platform').value;
    
    if (!category) {
        showError('Please enter a category');
        return;
    }

    showLoading();
    hideError();
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: category,
                target_platform: platform || 'any'
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        callback(data);
        showResults();
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
}

function displayKeywordResults(data) {
    displayJSONResults('seed-content', data.seed_keywords);
    displayJSONResults('competitor-content', data.competitor_gaps);
    displayJSONResults('questions-content', data.question_keywords);
    showTab('seed');
}

function displayReportResults(data) {
    document.getElementById('report-content').textContent = data.report;
    displayKeywordResults(data.keywords);
    showTab('report');
}

function displayJSONResults(containerId, data) {
    const container = document.getElementById(containerId);
    container.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
}

function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, 
        function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
}

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).style.display = 'block';
    document.querySelector(`button[data-tab="${tabId}"]`).classList.add('active');
}

function showLoading() {
    loading.style.display = 'block';
}

function hideLoading() {
    loading.style.display = 'none';
}

function showResults() {
    results.style.display = 'block';
}

function showError(message) {
    error.textContent = message;
    error.style.display = 'block';
}

function hideError() {
    error.style.display = 'none';
}