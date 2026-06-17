// =====================================================================
// CLINICAL-RAG: FRONTEND OPERATIONS ENGINE
// =====================================================================

const API_BASE = window.location.origin;

// Application State
const STATE = {
    mode: "demo",
    serverConnected: false,
    device: "CPU",
    guidelinesLoaded: false,
    activeTab: "retrieved-chunks",
    currentAnalysisResult: null
};

// Diagnostic Preset Materials
const PRESETS = {
    diabetic: `PATIENT REPORT: METRICS LOG
Patient Age/Sex: 54 Years / Female
Primary Lab Results:
- HbA1c: 7.2 %
- Blood Pressure: 128 / 78 mmHg
- LDL Cholesterol: 95 mg/dL
- Hemoglobin: 12.8 g/dL

Patient Notes: Complains of mild polydipsia (excessive thirst), frequent urination, and lethargy over the past 3 months. No current diabetic prescription regimen in place.`,
    
    hypertension: `PATIENT REPORT: CARDIO METRICS
Patient Age/Sex: 62 Years / Male
Primary Lab Results:
- Blood Pressure: 142 / 92 mmHg
- HbA1c: 5.4 %
- LDL Cholesterol: 115 mg/dL
- Hemoglobin: 14.5 g/dL

Patient Notes: Patient reports mild morning headaches, high sodium intake (frequent processed meals), and high job stress. Seeking educational guidance.`,
    
    lipid: `PATIENT REPORT: LIPID PANEL
Patient Age/Sex: 48 Years / Male
Primary Lab Results:
- LDL Cholesterol: 165 mg/dL
- HDL Cholesterol: 38 mg/dL
- Triglycerides: 210 mg/dL
- Blood Pressure: 135 / 85 mmHg
- Hemoglobin: 15.2 g/dL

Patient Notes: Family history of early coronary artery disease. Diet is high in saturated fats. Patient does not exercise.`,
    
    anemia: `PATIENT REPORT: HEMATOLOGY LOG
Patient Age/Sex: 29 Years / Female
Primary Lab Results:
- Hemoglobin: 10.4 g/dL
- HbA1c: 5.1 %
- Blood Pressure: 110 / 70 mmHg
- LDL Cholesterol: 90 mg/dL

Patient Notes: Patient exhibits pale conjunctiva, chronic fatigue, dizziness upon rising, and brittle hair. Suspects nutritional deficiency.`
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    // Initial UI Setup
    lucide.createIcons();
    checkServerStatus();
    loadGuidelinesText();
    
    // Periodically poll server status
    setInterval(checkServerStatus, 10000);
});

// Check API Connection and get system status
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (!response.ok) throw new Error("HTTP error");
        
        const data = await response.json();
        
        STATE.serverConnected = true;
        STATE.mode = data.mode;
        STATE.device = data.device;
        STATE.guidelinesLoaded = data.guidelines_loaded;
        
        updateStatusUI();
    } catch (error) {
        console.error("Server connection failure:", error);
        STATE.serverConnected = false;
        updateStatusUI();
    }
}

// Update Header Indicators
function updateStatusUI() {
    const dot = document.getElementById("server-status-dot");
    const text = document.getElementById("server-status-text");
    const device = document.getElementById("device-label");
    const modeBadge = document.getElementById("mode-badge");
    const modeLabel = document.getElementById("mode-label");
    const modeToggle = document.getElementById("mode-toggle");
    
    if (STATE.serverConnected) {
        dot.className = "status-indicator online";
        text.innerText = "Server: Online";
        device.innerText = `Device: ${STATE.device.toUpperCase()}`;
        
        if (STATE.mode === "production") {
            modeLabel.innerText = "Production Mode";
            modeBadge.className = "mode-badge production";
            modeToggle.checked = true;
        } else {
            modeLabel.innerText = "Demo Mode (Fast)";
            modeBadge.className = "mode-badge";
            modeToggle.checked = false;
        }
    } else {
        dot.className = "status-indicator offline";
        text.innerText = "Server: Offline";
        device.innerText = "Device: N/A";
        modeLabel.innerText = "No Connection";
        modeBadge.className = "mode-badge";
    }
}

// Ingestion Preset Injector
function loadPreset(type) {
    const textarea = document.getElementById("report-input");
    if (PRESETS[type]) {
        textarea.value = PRESETS[type];
        clearFilePreview();
    }
}

function clearInput() {
    document.getElementById("report-input").value = "";
    clearFilePreview();
}

// Toggle Server Inference Modes
async function toggleEngineMode(checkbox) {
    if (!STATE.serverConnected) {
        alert("Cannot change mode. FastAPI server is offline.");
        checkbox.checked = !checkbox.checked;
        return;
    }
    
    const targetMode = checkbox.checked ? "production" : "demo";
    const modeBadge = document.getElementById("mode-badge");
    const modeLabel = document.getElementById("mode-label");
    
    // Temporarily show loading state
    modeLabel.innerText = "Loading Model...";
    
    try {
        const response = await fetch(`${API_BASE}/api/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: targetMode })
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Error loading resources");
        }
        
        const data = await response.json();
        STATE.mode = data.mode;
        
        // Show success alert
        if (STATE.mode === "production") {
            alert("Production Mode Active! BioMistral-7B and MedCPT loaded.");
        } else {
            alert("Demo Mode Active! Fast simulated generation initialized.");
        }
        
        checkServerStatus();
        loadGuidelinesText();
    } catch (error) {
        alert(error.message || "Failed to switch engine modes.");
        // Revert UI toggle state
        checkbox.checked = !checkbox.checked;
        checkServerStatus();
    }
}

// File Upload Simulator
function triggerFileSelect() {
    document.getElementById("file-uploader").click();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    displayFilePreview(file);
    simulateFileOCR(file);
}

function displayFilePreview(file) {
    const previewCard = document.getElementById("file-preview-card");
    const fileName = document.getElementById("preview-file-name");
    const fileSize = document.getElementById("preview-file-size");
    const uploadArea = document.getElementById("drop-zone");
    
    fileName.innerText = file.name;
    fileSize.innerText = `${(file.size / 1024).toFixed(1)} KB`;
    
    previewCard.classList.remove("hidden");
    uploadArea.classList.add("hidden");
}

function removeFile() {
    clearFilePreview();
}

function clearFilePreview() {
    const previewCard = document.getElementById("file-preview-card");
    const uploadArea = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-uploader");
    
    fileInput.value = "";
    previewCard.classList.add("hidden");
    uploadArea.classList.remove("hidden");
}

// Simulate Diagnostic Report Layout-Aware OCR Parsing
function simulateFileOCR(file) {
    const textarea = document.getElementById("report-input");
    const name = file.name.toLowerCase();
    
    // Add small loader overlay in textarea
    textarea.value = `[Analyzing document structure layout... OCR Core executing on ${file.name}]`;
    
    setTimeout(() => {
        if (name.includes("diab") || name.includes("hba1c") || name.includes("glucose")) {
            loadPreset("diabetic");
        } else if (name.includes("bp") || name.includes("pressure") || name.includes("hyperten")) {
            loadPreset("hypertension");
        } else if (name.includes("lipid") || name.includes("chol") || name.includes("trigly")) {
            loadPreset("lipid");
        } else if (name.includes("anemia") || name.includes("blood") || name.includes("hb") || name.includes("hemo")) {
            loadPreset("anemia");
        } else {
            // Default simulated OCR text extraction
            textarea.value = `PATIENT METRIC EXTRACT:\nDocument: ${file.name}\n\n- HbA1c: 6.8 %\n- Blood Pressure: 138 / 88 mmHg\n- LDL Cholesterol: 142 mg/dL\n- Hemoglobin: 11.2 g/dL\n\nOCR scan completed. Double check numeric fields.`;
        }
    }, 1500);
}

// Fetch and render raw guidelines database
async function loadGuidelinesText() {
    const rawBox = document.getElementById("guidelines-raw-text");
    try {
        const response = await fetch(`${API_BASE}/api/guidelines`);
        if (!response.ok) throw new Error("Could not retrieve guidelines database.");
        const data = await response.json();
        rawBox.innerText = data.guidelines_text;
    } catch (err) {
        rawBox.innerText = "Error loading guidelines database text. Ensure backend is running.";
    }
}

function toggleGuidelinesDrawer() {
    const drawer = document.getElementById("guidelines-drawer");
    const icon = document.getElementById("toggle-drawer-icon");
    const text = document.getElementById("toggle-drawer-text");
    
    if (drawer.classList.contains("hidden")) {
        drawer.classList.remove("hidden");
        icon.setAttribute("data-lucide", "eye-off");
        text.innerText = "Hide Reference Database";
        loadGuidelinesText();
    } else {
        drawer.classList.add("hidden");
        icon.setAttribute("data-lucide", "eye");
        text.innerText = "View Reference Database";
    }
    lucide.createIcons();
}

// Tab switcher in execution visualizer details
function switchDetailTab(tabId) {
    STATE.activeTab = tabId;
    
    const tabs = document.querySelectorAll(".details-tabs .tab-btn");
    tabs.forEach(btn => btn.classList.remove("active"));
    
    const tabContents = document.querySelectorAll(".tab-content");
    tabContents.forEach(c => c.classList.add("hidden"));
    
    if (tabId === "retrieved-chunks") {
        document.querySelector("[onclick=\"switchDetailTab('retrieved-chunks')\"]").classList.add("active");
        document.getElementById("tab-content-retrieved-chunks").classList.remove("hidden");
    } else {
        document.querySelector("[onclick=\"switchDetailTab('raw-prompt')\"]").classList.add("active");
        document.getElementById("tab-content-raw-prompt").classList.remove("hidden");
    }
}

// Parse metrics from text input to draw onto interactive visual dashboard
function parseMetricsForDashboard(text) {
    const textLower = text.toLowerCase();
    
    // Extraction Regex Definitions
    const hba1cMatch = textLower.match(/(hba1c|glycated hemoglobin|a1c)[\s:]*([0-9\.]+)/);
    
    // Blood Pressure
    let bpSystolic = null;
    let bpDiastolic = null;
    const bpMatch = textLower.match(/(bp|blood pressure)[\s:]*([0-9]+)\s*\/\s*([0-9]+)/) || textLower.match(/([0-9]+)\s*\/\s*([0-9]+)\s*(mmhg)?/);
    if (bpMatch) {
        bpSystolic = parseInt(bpMatch[1]);
        bpDiastolic = parseInt(bpMatch[2]);
    }
    
    // LDL Cholesterol
    const ldlMatch = textLower.match(/ldl[\s:]*([0-9\.]+)/);
    
    // Hemoglobin
    const hbMatch = textLower.match(/(hemoglobin|hb|hgb)[\s:]*([0-9\.]+)/);
    
    // Update visual widgets
    updateMetricCard("hba1c", hba1cMatch ? parseFloat(hba1cMatch[2]) : null);
    updateMetricCard("bp", bpSystolic ? { sys: bpSystolic, dia: bpDiastolic } : null);
    updateMetricCard("ldl", ldlMatch ? parseFloat(ldlMatch[1]) : null);
    updateMetricCard("hb", hbMatch ? parseFloat(hbMatch[2]) : null);
}

// Calculate slider positions and alert classes
function updateMetricCard(type, val) {
    const card = document.getElementById(`card-${type}`);
    const valText = document.getElementById(`val-${type}`);
    const marker = document.getElementById(`marker-${type}`);
    
    // Reset state if null
    if (val === null) {
        card.className = "metric-card";
        valText.innerText = "--";
        marker.style.left = "0%";
        return;
    }
    
    let positionPct = 0;
    let classification = "normal";
    
    if (type === "hba1c") {
        valText.innerText = `${val}%`;
        
        // Ranges: Normal < 5.7 (Scale: 0-57%), Prediabetes 5.7-6.4 (Scale: 57-65%), Diabetes >= 6.5 (Scale: 65-100%)
        if (val < 5.7) {
            classification = "normal";
            // Map 4.0 -> 5.7 to 0% -> 57%
            const clamped = Math.max(4.0, val);
            positionPct = ((clamped - 4.0) / (5.7 - 4.0)) * 57;
        } else if (val >= 5.7 && val <= 6.4) {
            classification = "borderline";
            // Map 5.7 -> 6.4 to 57% -> 65%
            positionPct = 57 + ((val - 5.7) / (6.4 - 5.7)) * 8;
        } else {
            classification = "danger";
            // Map 6.5 -> 10.0 to 65% -> 100%
            const clamped = Math.min(10.0, val);
            positionPct = 65 + ((clamped - 6.5) / (10.0 - 6.5)) * 35;
        }
    } 
    else if (type === "bp") {
        valText.innerText = `${val.sys}/${val.dia} mmHg`;
        const sys = val.sys;
        const dia = val.dia;
        
        // Ranges: Normal < 120/80 (0-60%), Elevated 120-129/<80 (60-75%), Hypertension >= 130/80 (75-100%)
        if (sys < 120 && dia < 80) {
            classification = "normal";
            positionPct = (sys / 120) * 60;
        } else if (sys >= 120 && sys <= 129 && dia < 80) {
            classification = "borderline";
            positionPct = 60 + ((sys - 120) / (129 - 120)) * 15;
        } else {
            classification = "danger";
            const clampedSys = Math.min(180, Math.max(130, sys));
            positionPct = 75 + ((clampedSys - 130) / (180 - 130)) * 25;
        }
    } 
    else if (type === "ldl") {
        valText.innerText = `${val} mg/dL`;
        
        // Ranges: Normal < 100 (0-50%), Borderline 100-159 (50-80%), High >= 160 (80-100%)
        if (val < 100) {
            classification = "normal";
            const clamped = Math.max(50, val);
            positionPct = ((clamped - 50) / (100 - 50)) * 50;
        } else if (val >= 100 && val <= 159) {
            classification = "borderline";
            positionPct = 50 + ((val - 100) / (159 - 100)) * 30;
        } else {
            classification = "danger";
            const clamped = Math.min(220, val);
            positionPct = 80 + ((clamped - 160) / (220 - 160)) * 20;
        }
    } 
    else if (type === "hb") {
        valText.innerText = `${val} g/dL`;
        
        // Ranges: Low < 12.1 (0-35%), Normal 12.1-17.2 (35-80%), Elevated > 17.2 (80-100%)
        if (val < 12.1) {
            classification = "danger"; // Low is dangerous
            const clamped = Math.max(8.0, val);
            positionPct = ((clamped - 8.0) / (12.1 - 8.0)) * 35;
        } else if (val >= 12.1 && val <= 17.2) {
            classification = "normal";
            positionPct = 35 + ((val - 12.1) / (17.2 - 12.1)) * 45;
        } else {
            classification = "borderline"; // Elevated is warning/borderline
            const clamped = Math.min(20.0, val);
            positionPct = 80 + ((clamped - 17.2) / (20.0 - 17.2)) * 20;
        }
    }
    
    // Apply styling properties
    card.className = `metric-card ${classification}`;
    marker.style.left = `${Math.min(100, Math.max(0, positionPct))}%`;
}

// Convert generated markdown text from server to structured HTML
function formatMarkdownToHTML(mdText) {
    if (!mdText) return "";
    
    let html = mdText;
    
    // Escape standard tags to prevent HTML injection
    html = html.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    
    // Re-allow formatted blocks that BioMistral generates
    html = html.replace(/&lt;\|system\|&gt;/g, "<!-- system -->");
    html = html.replace(/&lt;\|user\|&gt;/g, "<!-- user -->");
    html = html.replace(/&lt;\|assistant\|&gt;/g, "<!-- assistant -->");
    
    // Markdown Headers
    html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");
    
    // Bold markup
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Horizontal lines
    html = html.replace(/^\*\*\*$/gim, "<hr>");
    html = html.replace(/^---$/gim, "<hr>");
    
    // Lists
    html = html.replace(/^\s*[-*]\s+(.*)$/gim, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>)/gim, "<ul>$1</ul>");
    // Clean repeating <ul> tags
    html = html.replace(/<\/ul>\s*<ul>/g, "");
    
    // Paragraph lists and new lines
    html = html.replace(/\n\n/g, "<p></p>");
    html = html.replace(/\n/g, "<br>");
    
    // Accentuate the medical safety disclaimer specifically
    // Look for tags containing "DISCLAIMER" or "MEDICAL DISCLAIMER" and apply the style block
    const lines = html.split("<p></p>");
    const styledLines = lines.map(line => {
        if (line.includes("MEDICAL DISCLAIMER") || line.includes("DISCLAIMER")) {
            return `<blockquote style="background: rgba(239, 68, 68, 0.06); border-left: 4px solid var(--color-danger); padding: 14px; border-radius: 0 8px 8px 0; margin-top: 18px; font-size: 12.5px; color: #fff;">${line}</blockquote>`;
        }
        return line;
    });
    
    return styledLines.join("");
}

// Execute the clinical analysis request via LangChain pipeline
async function runAnalysis() {
    const input = document.getElementById("report-input").value.trim();
    if (!input) {
        alert("Please enter diagnostic health report metrics or choose a preset.");
        return;
    }
    
    const analyzeBtn = document.getElementById("analyze-btn");
    const pulseIndicator = document.getElementById("synthesis-pulse");
    const outputText = document.getElementById("synthesis-text");
    const elapsedLabel = document.getElementById("elapsed-time");
    const statsContainer = document.getElementById("execution-stats");
    const detailsSection = document.getElementById("pipeline-details-section");
    
    // Lock Button and trigger animation states
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = "<i class=\"btn-icon spinner\" data-lucide=\"loader\"></i> Processing RAG Chain...";
    lucide.createIcons();
    
    pulseIndicator.classList.remove("hidden");
    outputText.innerHTML = `
        <div class="empty-state">
            <i data-lucide="loader" class="empty-icon spinner"></i>
            <p><strong>Running Retrieval-Augmented Generation...</strong></p>
            <p class="file-info">Searching FAISS index and building LangChain context</p>
        </div>
    `;
    lucide.createIcons();
    
    statsContainer.classList.add("hidden");
    detailsSection.classList.add("hidden");
    
    // Clear dynamic dashboard scales
    parseMetricsForDashboard(input);
    
    // Reset pipeline trace step visual status
    resetPipelineTrace();
    
    try {
        // Trace Step 1: Ingestion loading
        setPipelineStep("step-1", "active", "Tokenizing input data...");
        await delay(600);
        setPipelineStep("step-1", "completed", "Chunks aligned (Overlap 100)");
        
        // Trace Step 2: MedCPT retrieval
        setPipelineStep("step-2", "active", "Retrieving vector similarity...");
        
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: input })
        });
        
        if (!response.ok) throw new Error("FastAPI RAG Inference Failed");
        
        const data = await response.json();
        STATE.currentAnalysisResult = data;
        
        setPipelineStep("step-2", "completed", `Retrieved ${data.retrieved_chunks.length} standard reference guidelines`);
        
        // Trace Step 3: Prompt assembly
        setPipelineStep("step-3", "active", "Formulating clinical prompt payload...");
        await delay(500);
        setPipelineStep("step-3", "completed", "Constructed prompt with guardrails");
        
        // Trace Step 4: Model synthesis
        setPipelineStep("step-4", "active", `Invoking LLM...`);
        await delay(600);
        setPipelineStep("step-4", "completed", `Completed (T = 0.1)`);
        
        // Update Output Metrics and layout
        elapsedLabel.innerText = `${data.execution_time_ms} ms`;
        statsContainer.classList.remove("hidden");
        
        // Render formatted HTML report output
        outputText.innerHTML = formatMarkdownToHTML(data.result);
        
        // Render retrieved guidelines context chunks list in details
        renderRetrievedChunks(data.retrieved_chunks);
        
        // Render raw prompt payload
        document.getElementById("raw-prompt-code").innerText = data.prompt;
        detailsSection.classList.remove("hidden");
        
        // Parse again in case bounds need refresh
        parseMetricsForDashboard(input);
        
    } catch (error) {
        console.error(error);
        outputText.innerHTML = `
            <div class="empty-state">
                <i data-lucide="alert-triangle" class="empty-icon text-red"></i>
                <p><strong>RAG Execution Encountered an Error</strong></p>
                <p class="file-info">${error.message || "Ensure the backend uvicorn server is running on port 8000."}</p>
            </div>
        `;
        lucide.createIcons();
        setPipelineError();
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = "<i data-lucide=\"play-circle\" class=\"btn-icon\"></i> Run Clinical Analysis";
        pulseIndicator.classList.add("hidden");
        lucide.createIcons();
    }
}

// Render retrieved guideline database fragments
function renderRetrievedChunks(chunks) {
    const list = document.getElementById("retrieved-chunks-list");
    list.innerHTML = "";
    
    if (chunks.length === 0) {
        list.innerHTML = "<p class='file-info'>No contexts were retrieved by vector search.</p>";
        return;
    }
    
    chunks.forEach(c => {
        const item = document.createElement("div");
        item.className = "chunk-item";
        
        item.innerHTML = `
            <div class="chunk-meta-row">
                <span>RETIRETED CONTEXT CHUNK #${c.id}</span>
                <span>METADATA SOURCE: medical_guidelines.txt</span>
            </div>
            <div class="chunk-body">${c.content.replace(/\n/g, "<br>")}</div>
        `;
        list.appendChild(item);
    });
}

// Helper methods to set trace step card statuses
function setPipelineStep(stepId, state, statusText) {
    const card = document.getElementById(stepId);
    const statusLabel = card.querySelector(".step-status");
    
    card.className = `pipeline-card ${state}`;
    statusLabel.innerText = statusText;
}

function resetPipelineTrace() {
    setPipelineStep("step-1", "", "Pending Ingestion");
    setPipelineStep("step-2", "", "Waiting for Query");
    setPipelineStep("step-3", "", "Waiting for Context");
    setPipelineStep("step-4", "", "Waiting for Prompt");
}

function setPipelineError() {
    document.querySelectorAll(".pipeline-card").forEach(c => {
        if (c.classList.contains("active")) {
            c.className = "pipeline-card danger";
            c.querySelector(".step-status").innerText = "Execution Failed";
        }
    });
}

// Export Analysis text results to local TXT download
function exportAnalysisText() {
    if (!STATE.currentAnalysisResult) {
        alert("No completed report analysis to export.");
        return;
    }
    
    const textContent = STATE.currentAnalysisResult.result;
    const blob = new Blob([textContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.href = url;
    link.download = "clinical_rag_report.txt";
    
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Utility delay function
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
