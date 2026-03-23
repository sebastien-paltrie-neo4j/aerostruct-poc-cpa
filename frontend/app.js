const API_BASE = '';

let baselineData = null;
let incidentData = null;
let isSyncing = false;

const baselineTimings = [];
const incidentTimings = [];

function pushTiming(arr, ms, backend) {
    arr.unshift({ ms, backend });
    if (arr.length > 3) arr.pop();
}

function renderTimings(elementId, arr) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = arr.map(t =>
        `<span class="timing-pill">${t.ms}ms (${t.backend})</span>`
    ).join('');
}

// DOM elements
const rootInput = document.getElementById('root');
const incidentSelect = document.getElementById('incidentWo');
const delayInput = document.getElementById('delayDays');
const loadBaselineBtn = document.getElementById('loadBaseline');
const loadIncidentBtn = document.getElementById('loadIncident');
const errorDiv = document.getElementById('errorMessage');
const filterCriticalToggle = document.getElementById('filterCritical');
const algoGdsRadio = document.getElementById('algoGds');

// Utils
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => errorDiv.style.display = 'none', 5000);
}

function filterTasks(tasks) {
    return filterCriticalToggle.checked ? tasks.filter(t => t.isCritical) : tasks;
}

// Transform tasks for Frappe Gantt format
function transformTasksForGantt(tasks) {
    const taskIds = new Set(tasks.map(t => String(t.id)));
    
    return tasks.map(task => {
        let customClass = '';
        if (task.isCritical && task.isIncident) customClass = 'critical-incident';
        else if (task.isCritical) customClass = 'critical';
        else if (task.isIncident) customClass = 'incident';
        
        const deps = (task.dependencies || '')
            .split(',')
            .map(d => d.trim())
            .filter(d => d && taskIds.has(d))
            .join(',');
        
        return {
            id: String(task.id),
            name: task.name,
            start: task.start?.split('T')[0] || new Date().toISOString().split('T')[0],
            end: task.end?.split('T')[0] || new Date().toISOString().split('T')[0],
            dependencies: deps,
            custom_class: customClass
        };
    });
}

// Render Gantt chart
function renderGantt(containerId, tasks) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (!tasks?.length) {
        container.innerHTML = '<div class="gantt-placeholder">No data</div>';
        return null;
    }
    
    try {
        const gantt = new Gantt(`#${containerId}`, transformTasksForGantt(tasks), {
            view_mode: 'Day',
            date_format: 'YYYY-MM-DD',
            container_height: 500,
            upper_header_height: 30,
            lower_header_height: 20,
            scroll_to: 'start',
            language: 'en',
            popup_trigger: 'click',
            custom_popup_html: (task) => {
                const t = tasks.find(x => x.id === task.id);
                return `
                    <div class="details-container">
                        <h5>${task.name}</h5>
                        <p>Duration: ${t?.duration_days ?? '-'} days</p>
                        <p>Critical: ${t?.isCritical ? 'Yes' : 'No'}</p>
                        <p>Incident: ${t?.isIncident ? 'Yes' : 'No'}</p>
                    </div>
                `;
            }
        });
        
        return gantt;
    } catch (e) {
        console.error('Error rendering Gantt:', e);
        container.innerHTML = `<div class="gantt-placeholder">Error: ${e.message}</div>`;
        return null;
    }
}

// Update KPI display
function updateKPIs() {
    if (baselineData) {
        document.getElementById('kpiBaseline').textContent = baselineData.totalDuration;
    }
    
    if (incidentData) {
        document.getElementById('kpiIncident').textContent = incidentData.totalDuration;
        if (baselineData) {
            const delta = incidentData.totalDuration - baselineData.totalDuration;
            document.getElementById('kpiDelta').textContent = delta > 0 ? `+${delta}` : delta;
        }
    } else {
        document.getElementById('kpiIncident').textContent = '-';
        document.getElementById('kpiDelta').textContent = '-';
    }
}

// Populate incident dropdown
function populateIncidentDropdown(tasks) {
    incidentSelect.innerHTML = '<option value="">-- Select a WO --</option>';
    tasks.forEach(task => {
        const option = document.createElement('option');
        option.value = task.id;
        option.textContent = task.id + (task.isCritical ? ' (critical)' : '');
        incidentSelect.appendChild(option);
    });
    incidentSelect.disabled = false;
    delayInput.disabled = false;
    loadIncidentBtn.disabled = false;
}

// Scroll sync between Gantt charts
function setupScrollSync() {
    const baselineScroll = document.querySelector('#ganttBaseline .gantt-container');
    const incidentScroll = document.querySelector('#ganttIncident .gantt-container');
    if (!baselineScroll || !incidentScroll) return;
    
    function syncScroll(source, target) {
        if (isSyncing) return;
        isSyncing = true;
        target.scrollLeft = source.scrollLeft;
        target.scrollTop = source.scrollTop;
        setTimeout(() => isSyncing = false, 50);
    }
    
    function propagateWheel(e) {
        e.preventDefault();
        window.scrollBy(0, e.deltaY);
    }
    
    baselineScroll.addEventListener('scroll', () => syncScroll(baselineScroll, incidentScroll));
    incidentScroll.addEventListener('scroll', () => syncScroll(incidentScroll, baselineScroll));
    baselineScroll.addEventListener('wheel', propagateWheel, { passive: false });
    incidentScroll.addEventListener('wheel', propagateWheel, { passive: false });
}

// Refresh both Gantt charts
function refreshGantts() {
    if (baselineData) renderGantt('ganttBaseline', filterTasks(baselineData.tasks));
    if (incidentData) renderGantt('ganttIncident', filterTasks(incidentData.tasks));
    if (baselineData && incidentData) setTimeout(setupScrollSync, 100);
}

// Load baseline
async function loadBaseline() {
    const root = rootInput.value.trim();
    if (!root) return showError('Please enter a root WorkOrder');
    
    errorDiv.style.display = 'none';
    loadBaselineBtn.disabled = true;
    loadBaselineBtn.textContent = 'Loading...';
    
    try {
        const useGds = algoGdsRadio.checked;
        const t0 = Date.now();
        const res = await fetch(`${API_BASE}/gantt/baseline?root=${encodeURIComponent(root)}${useGds ? '&useGds=true' : ''}`);
        if (!res.ok) throw new Error((await res.json()).detail || 'Server error');
        
        baselineData = await res.json();
        incidentData = null;

        pushTiming(baselineTimings, Date.now() - t0, useGds ? 'GDS' : 'Cypher');
        renderTimings('baselineTimings', baselineTimings);
        
        renderGantt('ganttBaseline', filterTasks(baselineData.tasks));
        document.getElementById('ganttIncident').innerHTML = 
            '<div class="gantt-placeholder">Select an incident WO and click "Simulate"</div>';
        
        populateIncidentDropdown(baselineData.tasks);
        updateKPIs();
    } catch (e) {
        showError(e.message);
    } finally {
        loadBaselineBtn.disabled = false;
        loadBaselineBtn.textContent = 'Load Baseline';
    }
}

// Load incident simulation
async function loadIncident() {
    const root = rootInput.value.trim();
    const incidentWo = incidentSelect.value;
    const delayDays = parseFloat(delayInput.value) || 0;
    
    if (!incidentWo) return showError('Please select an incident WorkOrder');
    
    errorDiv.style.display = 'none';
    loadIncidentBtn.disabled = true;
    loadIncidentBtn.textContent = 'Loading...';
    
    try {
        const useGds = algoGdsRadio.checked;
        const url = `${API_BASE}/gantt/incident?root=${encodeURIComponent(root)}&incidentWo=${encodeURIComponent(incidentWo)}&delayDays=${delayDays}${useGds ? '&useGds=true' : ''}`;
        const t0 = Date.now();
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json()).detail || 'Server error');
        
        incidentData = await res.json();

        pushTiming(incidentTimings, Date.now() - t0, useGds ? 'GDS' : 'Cypher');
        renderTimings('incidentTimings', incidentTimings);

        renderGantt('ganttIncident', filterTasks(incidentData.tasks));
        updateKPIs();
        setTimeout(setupScrollSync, 100);
    } catch (e) {
        showError(e.message);
    } finally {
        loadIncidentBtn.disabled = false;
        loadIncidentBtn.textContent = 'Simulate';
    }
}

// Event listeners
loadBaselineBtn.addEventListener('click', loadBaseline);
loadIncidentBtn.addEventListener('click', loadIncident);
filterCriticalToggle.addEventListener('change', refreshGantts);
rootInput.addEventListener('keypress', e => e.key === 'Enter' && loadBaseline());
