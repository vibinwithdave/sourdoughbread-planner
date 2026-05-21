/**
 * Sourdough Bread Planner - Frontend Application
 * 
 * Primary input: Starter Amount (g)
 * Fermentation Speed (slow/regular/fast) defines the ratio between starter, water, and flour.
 * Flour and water are calculated from: starter_amount * (flour_ratio / starter_ratio)
 */

// Speed ratios based on Alexandra Cooks recipe
// slow:    50g starter : 375g water : 500g flour
// regular: 75g starter : 375g water : 500g flour
// fast:   100g starter : 375g water : 500g flour
const SPEED_RATIOS = {
    slow:    { starter: 50,  water: 375, flour: 500 },
    regular: { starter: 75,  water: 375, flour: 500 },
    fast:    { starter: 100, water: 375, flour: 500 }
};

// Store the current timeline data (flat list) for editing
let currentTimelineFlat = [];
let currentSettings = {};
let currentIngredients = {};

document.addEventListener('DOMContentLoaded', function () {
    initializeForm();
    attachEventListeners();
    updateRecipePreview();
    loadSavedSchedules();
});

// --- Initialization ---

function initializeForm() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    const minutesStr = minutes < 10 ? '0' + minutes : String(minutes);
    const currentTime = `${hours}:${minutesStr} ${ampm}`;

    document.getElementById('start_time').value = currentTime;
    document.getElementById('currentTimeHint').textContent = `Current time: ${currentTime}`;

    updateBulkEstimate();
    updateStarterPreview();
}

function attachEventListeners() {
    // Form submission
    document.getElementById('scheduleForm').addEventListener('submit', handleFormSubmit);

    // Primary inputs that trigger recipe recalculation
    document.getElementById('starter_amount').addEventListener('input', function () {
        updateRecipePreview();
        updateStarterPreview();
    });

    document.getElementById('fermentation_speed').addEventListener('change', function () {
        handleSpeedChange();
        updateRecipePreview();
    });

    document.getElementById('salt_percent').addEventListener('input', updateRecipePreview);

    // Custom mode inputs
    const customInputs = document.querySelectorAll('#starter_percent, #hydration');
    customInputs.forEach(el => {
        if (el) el.addEventListener('input', updateRecipePreview);
    });

    // Temperature change -> update bulk estimate
    document.getElementById('temperature_f').addEventListener('input', updateBulkEstimate);

    // Starter maintenance inputs
    document.getElementById('existing_starter_amount').addEventListener('input', updateStarterPreview);
    document.getElementById('feeding_ratio').addEventListener('change', updateStarterPreview);

    // Save and Export buttons
    document.getElementById('saveScheduleBtn').addEventListener('click', saveSchedule);
    document.getElementById('exportScheduleBtn').addEventListener('click', exportSchedule);
}

// --- Speed Mode Handling ---

function handleSpeedChange() {
    const speed = document.getElementById('fermentation_speed').value;
    const customFields = document.querySelectorAll('.custom-only');

    if (speed === 'custom') {
        // Show custom percentage fields
        customFields.forEach(el => el.style.display = '');
    } else {
        // Hide custom fields
        customFields.forEach(el => el.style.display = 'none');
    }
}

// --- Live Recipe Preview ---

function updateRecipePreview() {
    const starterAmount = parseFloat(document.getElementById('starter_amount').value) || 100;
    const speed = document.getElementById('fermentation_speed').value;
    const saltPercent = parseFloat(document.getElementById('salt_percent').value) || 2.2;

    let totalFlour, totalWater;

    if (speed !== 'custom' && SPEED_RATIOS[speed]) {
        // Speed-based: scale flour and water from the ratio
        const ratio = SPEED_RATIOS[speed];
        const scaleFactor = starterAmount / ratio.starter;
        totalFlour = ratio.flour * scaleFactor;
        totalWater = ratio.water * scaleFactor;
    } else {
        // Custom: use starter % and hydration %
        const starterPercent = parseFloat(document.getElementById('starter_percent').value) || 20;
        const hydration = parseFloat(document.getElementById('hydration').value) || 75;
        if (starterPercent <= 0) return;
        totalFlour = starterAmount / (starterPercent / 100);
        totalWater = totalFlour * (hydration / 100);
    }

    const salt = totalFlour * (saltPercent / 100);

    // Starter is 100% hydration: half flour, half water
    const additionalFlour = totalFlour - (starterAmount / 2);
    const additionalWater = totalWater - (starterAmount / 2);
    const totalDough = totalFlour + totalWater + salt + starterAmount;

    // Update preview display
    document.getElementById('previewFlour').textContent = `${Math.round(totalFlour)}g`;
    document.getElementById('previewWater').textContent = `${Math.round(totalWater)}g`;
    document.getElementById('previewSalt').textContent = `${roundTo(salt, 1)}g`;
    document.getElementById('previewStarter').textContent = `${Math.round(starterAmount)}g`;
    document.getElementById('previewTotal').textContent = `${Math.round(totalDough)}g`;

    // Update breakdown
    document.getElementById('previewAddFlour').textContent = Math.round(additionalFlour);
    document.getElementById('previewAddWater').textContent = Math.round(additionalWater);
    document.getElementById('previewAddStarter').textContent = Math.round(starterAmount);
    document.getElementById('previewAddSalt').textContent = roundTo(salt, 1);
}

// --- Live Updates ---

function updateBulkEstimate() {
    const temp = parseFloat(document.getElementById('temperature_f').value) || 70;
    const hours = estimateBulkHours(temp);
    document.getElementById('bulkEstimate').textContent = `~${hours} hours bulk fermentation`;
}

function estimateBulkHours(tempF) {
    const data = [
        [65, 12.0], [68, 10.0], [70, 9.0], [72, 8.0],
        [75, 7.0], [78, 6.0], [80, 5.0], [82, 4.5], [85, 4.0]
    ];

    if (tempF <= data[0][0]) return data[0][1];
    if (tempF >= data[data.length - 1][0]) return data[data.length - 1][1];

    for (let i = 0; i < data.length - 1; i++) {
        if (tempF >= data[i][0] && tempF <= data[i + 1][0]) {
            const fraction = (tempF - data[i][0]) / (data[i + 1][0] - data[i][0]);
            const hours = data[i][1] + fraction * (data[i + 1][1] - data[i][1]);
            return Math.round(hours * 10) / 10;
        }
    }
    return 9.0;
}

function updateStarterPreview() {
    const existingStarter = parseFloat(document.getElementById('existing_starter_amount').value) || 50;
    const ratio = document.getElementById('feeding_ratio').value;
    const starterAmount = parseFloat(document.getElementById('starter_amount').value) || 100;

    const parts = ratio.split(':').map(Number);
    const flourParts = parts[1];
    const waterParts = parts[2];

    const totalAfterFeeding = existingStarter + (existingStarter * flourParts) + (existingStarter * waterParts);
    const remaining = Math.max(0, totalAfterFeeding - starterAmount);

    let statusText = '';
    if (totalAfterFeeding >= starterAmount) {
        statusText = `Feeding ${existingStarter}g at ${ratio} produces ${Math.round(totalAfterFeeding)}g. ` +
            `Recipe needs ${Math.round(starterAmount)}g, leaving ${Math.round(remaining)}g for future bakes.`;
    } else {
        statusText = `Warning: Feeding ${existingStarter}g at ${ratio} only produces ${Math.round(totalAfterFeeding)}g, ` +
            `but recipe needs ${Math.round(starterAmount)}g. Increase existing starter amount or change ratio.`;
    }

    document.getElementById('starterPreview').textContent = statusText;
}

// --- Form Submission ---

async function handleFormSubmit(e) {
    e.preventDefault();

    const btn = e.target.querySelector('button[type="submit"]');
    btn.textContent = 'Generating...';
    btn.disabled = true;

    try {
        const data = collectFormData();
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }

        const result = await response.json();

        if (result.success) {
            currentSettings = result.settings;
            currentIngredients = result.ingredients;
            // Flatten the timeline for editing
            currentTimelineFlat = flattenTimeline(result.timeline);
            displayResults(result);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error generating schedule: ' + error.message);
    } finally {
        btn.textContent = 'Generate Baking Schedule';
        btn.disabled = false;
    }
}

function collectFormData() {
    const speed = document.getElementById('fermentation_speed').value;

    // Collect enabled steps
    const enabledSteps = {
        'autolyse': document.getElementById('step_autolyse').checked,
        'rest_after_mix': document.getElementById('step_rest_after_mix').checked,
        'stretch_fold_1': document.getElementById('step_folds').checked,
        'stretch_fold_2': document.getElementById('step_folds').checked,
        'stretch_fold_3': document.getElementById('step_folds').checked,
        'stretch_fold_4': document.getElementById('step_folds').checked,
        'pre_shape': document.getElementById('step_pre_shape').checked,
        'bench_rest': document.getElementById('step_pre_shape').checked
    };

    const formData = {
        starter_amount: parseFloat(document.getElementById('starter_amount').value),
        fermentation_speed: speed,
        salt_percent: parseFloat(document.getElementById('salt_percent').value),
        existing_starter_amount: parseFloat(document.getElementById('existing_starter_amount').value),
        feeding_ratio: document.getElementById('feeding_ratio').value,
        start_time: document.getElementById('start_time').value,
        temperature_f: parseFloat(document.getElementById('temperature_f').value),
        cold_proof_hours: parseFloat(document.getElementById('cold_proof_hours').value),
        flour_type: document.getElementById('flour_type').value,
        enabled_steps: enabledSteps
    };

    // Include custom fields only in custom mode
    if (speed === 'custom') {
        formData.starter_percent = parseFloat(document.getElementById('starter_percent').value);
        formData.hydration = parseFloat(document.getElementById('hydration').value);
    }

    return formData;
}

// --- Results Display ---

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.style.display = 'block';

    renderIngredients(data.ingredients, data.settings);
    renderTimeline(data.timeline, data.settings);

    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderIngredients(ingredients, settings) {
    const feeding = ingredients.starter_feeding;

    document.getElementById('starterFeedingResults').innerHTML = `
        <div class="ingredient-row">
            <span class="label">Existing Starter</span>
            <span class="value">${feeding.existing_starter_used}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">+ Flour</span>
            <span class="value">${feeding.flour_to_add}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">+ Water</span>
            <span class="value">${feeding.water_to_add}g</span>
        </div>
        <div class="ingredient-row highlight">
            <span class="label">Total Active Starter</span>
            <span class="value">${feeding.total_after_feeding}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Used in Recipe</span>
            <span class="value">${feeding.starter_for_recipe}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Remaining (keep)</span>
            <span class="value">${feeding.starter_remaining}g</span>
        </div>
        <div class="starter-status ${feeding.sufficient ? 'sufficient' : 'insufficient'}">
            ${feeding.sufficient
                ? 'Feeding produces enough starter for the recipe'
                : 'Insufficient! Increase existing starter amount or change ratio'}
        </div>
    `;

    document.getElementById('mainDoughResults').innerHTML = `
        <div class="ingredient-row">
            <span class="label">Active Starter</span>
            <span class="value">${ingredients.starter_amount}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">${settings.flour_type}</span>
            <span class="value">${ingredients.additional_flour}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Water</span>
            <span class="value">${ingredients.additional_water}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Salt</span>
            <span class="value">${ingredients.salt}g</span>
        </div>
    `;

    document.getElementById('totalsResults').innerHTML = `
        <div class="ingredient-row">
            <span class="label">Total Flour</span>
            <span class="value">${ingredients.total_flour_weight}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Total Water</span>
            <span class="value">${ingredients.total_water}g</span>
        </div>
        <div class="ingredient-row">
            <span class="label">Hydration</span>
            <span class="value">${ingredients.actual_hydration}%</span>
        </div>
        <div class="ingredient-row highlight">
            <span class="label">Total Dough Weight</span>
            <span class="value">${ingredients.total_dough_weight}g</span>
        </div>
    `;
}

function renderTimeline(days, settings) {
    document.getElementById('timelineInfo').innerHTML = `
        <span class="timeline-badge"><strong>${settings.temperature_f}&deg;F</strong> kitchen</span>
        <span class="timeline-badge"><strong>~${settings.bulk_fermentation_estimate}h</strong> bulk ferment</span>
        <span class="timeline-badge"><strong>${settings.cold_proof_hours}h</strong> cold proof</span>
        <span class="timeline-badge"><strong>${settings.hydration}%</strong> hydration</span>
        <span class="timeline-badge"><strong>${settings.fermentation_speed}</strong> speed</span>
    `;

    let html = '';
    let globalIndex = 0;

    days.forEach(day => {
        html += `<div class="timeline-day">`;
        html += `<div class="timeline-day-header">${day.date}</div>`;
        html += `<div class="timeline-steps">`;

        day.steps.forEach(step => {
            html += `
                <div class="timeline-step" data-category="${step.category}" data-step-index="${globalIndex}" data-step-id="${step.step_id}">
                    <div class="step-header">
                        <span class="step-name">${step.name}</span>
                        <span class="step-time editable-time" data-index="${globalIndex}" title="Click to edit time">${step.time_display}</span>
                    </div>
                    <div class="step-description">${step.description}</div>
                    <div class="step-visual-cue">${step.visual_cue}</div>
                    ${step.note ? `<div class="step-note">${step.note}</div>` : ''}
                </div>
            `;
            globalIndex++;
        });

        html += `</div></div>`;
    });

    document.getElementById('timelineVisual').innerHTML = html;

    // Attach click handlers for editable times
    document.querySelectorAll('.editable-time').forEach(el => {
        el.addEventListener('click', handleTimeClick);
    });
}

// --- Inline Time Editing ---

function handleTimeClick(e) {
    const timeEl = e.target;
    const stepIndex = parseInt(timeEl.dataset.index);
    const step = currentTimelineFlat[stepIndex];

    if (!step) return;

    // Create an inline time input
    const currentDt = new Date(step.datetime);
    const timeValue = formatForInput(currentDt);
    const dateValue = formatDateForInput(currentDt);

    const editContainer = document.createElement('div');
    editContainer.className = 'time-edit-container';
    editContainer.innerHTML = `
        <input type="date" class="time-edit-date" value="${dateValue}">
        <input type="time" class="time-edit-input" value="${timeValue}">
        <button class="time-edit-confirm" title="Apply">&#10003;</button>
        <button class="time-edit-cancel" title="Cancel">&#10005;</button>
    `;

    // Replace the time display with the edit controls
    timeEl.style.display = 'none';
    timeEl.parentNode.appendChild(editContainer);

    // Focus the time input
    editContainer.querySelector('.time-edit-input').focus();

    // Handle confirm
    editContainer.querySelector('.time-edit-confirm').addEventListener('click', async () => {
        const newDate = editContainer.querySelector('.time-edit-date').value;
        const newTime = editContainer.querySelector('.time-edit-input').value;
        if (newDate && newTime) {
            const newDatetime = `${newDate}T${newTime}:00`;
            await recalculateFromStep(stepIndex, newDatetime);
        }
        editContainer.remove();
        timeEl.style.display = '';
    });

    // Handle cancel
    editContainer.querySelector('.time-edit-cancel').addEventListener('click', () => {
        editContainer.remove();
        timeEl.style.display = '';
    });

    // Handle Enter key
    editContainer.querySelectorAll('input').forEach(input => {
        input.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                const newDate = editContainer.querySelector('.time-edit-date').value;
                const newTime = editContainer.querySelector('.time-edit-input').value;
                if (newDate && newTime) {
                    const newDatetime = `${newDate}T${newTime}:00`;
                    await recalculateFromStep(stepIndex, newDatetime);
                }
                editContainer.remove();
                timeEl.style.display = '';
            } else if (e.key === 'Escape') {
                editContainer.remove();
                timeEl.style.display = '';
            }
        });
    });
}

async function recalculateFromStep(stepIndex, newDatetime) {
    try {
        const response = await fetch('/api/recalculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                timeline: currentTimelineFlat,
                edited_step_index: stepIndex,
                new_datetime: newDatetime,
                temperature_f: currentSettings.temperature_f || 70,
                cold_proof_hours: currentSettings.cold_proof_hours || 24
            })
        });

        const result = await response.json();

        if (result.success) {
            currentTimelineFlat = flattenTimeline(result.timeline);
            renderTimeline(result.timeline, currentSettings);
        } else {
            alert('Error recalculating: ' + result.error);
        }
    } catch (error) {
        console.error('Recalculation error:', error);
        alert('Error recalculating timeline: ' + error.message);
    }
}

// --- Save Schedule ---

function saveSchedule() {
    if (currentTimelineFlat.length === 0) {
        alert('No schedule to save. Generate a baking schedule first.');
        return;
    }

    const name = prompt('Name this schedule:', `Bake - ${new Date().toLocaleDateString()}`);
    if (!name) return;

    const schedule = {
        id: Date.now(),
        name: name,
        savedAt: new Date().toISOString(),
        settings: currentSettings,
        ingredients: currentIngredients,
        timeline: currentTimelineFlat
    };

    // Get existing saved schedules
    const saved = JSON.parse(localStorage.getItem('sourdough_schedules') || '[]');
    saved.unshift(schedule);

    // Keep max 20 schedules
    if (saved.length > 20) saved.pop();

    localStorage.setItem('sourdough_schedules', JSON.stringify(saved));

    loadSavedSchedules();
    alert(`Schedule "${name}" saved!`);
}

function loadSavedSchedules() {
    const saved = JSON.parse(localStorage.getItem('sourdough_schedules') || '[]');
    const section = document.getElementById('savedSchedulesSection');
    const list = document.getElementById('savedSchedulesList');

    if (saved.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    let html = '';

    saved.forEach((schedule, index) => {
        const savedDate = new Date(schedule.savedAt).toLocaleString();
        const firstStep = schedule.timeline[0];
        const lastStep = schedule.timeline[schedule.timeline.length - 1];

        html += `
            <div class="saved-schedule-card">
                <div class="saved-schedule-header">
                    <strong>${schedule.name}</strong>
                    <span class="saved-date">${savedDate}</span>
                </div>
                <div class="saved-schedule-info">
                    ${schedule.settings.fermentation_speed || ''} speed &middot;
                    ${schedule.settings.temperature_f || ''}°F &middot;
                    ${schedule.settings.cold_proof_hours || ''}h cold proof
                </div>
                <div class="saved-schedule-actions">
                    <button class="action-btn-sm" onclick="loadSchedule(${index})">Load</button>
                    <button class="action-btn-sm delete-btn" onclick="deleteSchedule(${index})">Delete</button>
                </div>
            </div>
        `;
    });

    list.innerHTML = html;
}

function loadSchedule(index) {
    const saved = JSON.parse(localStorage.getItem('sourdough_schedules') || '[]');
    const schedule = saved[index];
    if (!schedule) return;

    currentSettings = schedule.settings;
    currentIngredients = schedule.ingredients;
    currentTimelineFlat = schedule.timeline;

    // Re-group timeline by day for rendering
    const grouped = groupTimelineByDay(currentTimelineFlat);

    const resultsDiv = document.getElementById('results');
    resultsDiv.style.display = 'block';

    renderIngredients(currentIngredients, currentSettings);
    renderTimeline(grouped, currentSettings);

    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function deleteSchedule(index) {
    if (!confirm('Delete this saved schedule?')) return;

    const saved = JSON.parse(localStorage.getItem('sourdough_schedules') || '[]');
    saved.splice(index, 1);
    localStorage.setItem('sourdough_schedules', JSON.stringify(saved));
    loadSavedSchedules();
}

// --- Export Schedule ---

function exportSchedule() {
    if (currentTimelineFlat.length === 0) {
        alert('No schedule to export. Generate a baking schedule first.');
        return;
    }

    let text = '=== SOURDOUGH BAKING SCHEDULE ===\n\n';

    // Add settings
    text += `Speed: ${currentSettings.fermentation_speed}\n`;
    text += `Kitchen Temp: ${currentSettings.temperature_f}°F\n`;
    text += `Bulk Fermentation: ~${currentSettings.bulk_fermentation_estimate}h\n`;
    text += `Cold Proof: ${currentSettings.cold_proof_hours}h\n`;
    text += `Hydration: ${currentSettings.hydration}%\n\n`;

    // Add ingredients
    text += '--- INGREDIENTS ---\n\n';
    if (currentIngredients.starter_feeding) {
        const f = currentIngredients.starter_feeding;
        text += `Starter Feeding:\n`;
        text += `  Existing starter: ${f.existing_starter_used}g\n`;
        text += `  + Flour: ${f.flour_to_add}g\n`;
        text += `  + Water: ${f.water_to_add}g\n`;
        text += `  = Total: ${f.total_after_feeding}g\n\n`;
    }
    text += `Main Dough:\n`;
    text += `  Starter: ${currentIngredients.starter_amount}g\n`;
    text += `  Flour: ${currentIngredients.additional_flour}g\n`;
    text += `  Water: ${currentIngredients.additional_water}g\n`;
    text += `  Salt: ${currentIngredients.salt}g\n`;
    text += `  Total Dough: ${currentIngredients.total_dough_weight}g\n\n`;

    // Add timeline
    text += '--- TIMELINE ---\n\n';

    const grouped = groupTimelineByDay(currentTimelineFlat);
    grouped.forEach(day => {
        text += `${day.date}\n`;
        text += '-'.repeat(day.date.length) + '\n';
        day.steps.forEach(step => {
            text += `  ${step.time_display.padEnd(10)} ${step.name}\n`;
            if (step.note) {
                text += `               ${step.note}\n`;
            }
        });
        text += '\n';
    });

    // Download as file
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sourdough-schedule-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// --- Utility Functions ---

function flattenTimeline(days) {
    const flat = [];
    days.forEach(day => {
        day.steps.forEach(step => {
            flat.push({ ...step });
        });
    });
    return flat;
}

function groupTimelineByDay(flatTimeline) {
    const days = {};
    flatTimeline.forEach(entry => {
        const dt = new Date(entry.datetime);
        const dateKey = entry.date_display || dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
        if (!days[dateKey]) {
            days[dateKey] = {
                date: dateKey,
                date_sort: dt.toISOString().slice(0, 10),
                steps: []
            };
        }
        days[dateKey].steps.push(entry);
    });

    return Object.values(days).sort((a, b) => a.date_sort.localeCompare(b.date_sort));
}

function formatForInput(dt) {
    const hours = String(dt.getHours()).padStart(2, '0');
    const minutes = String(dt.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function formatDateForInput(dt) {
    const year = dt.getFullYear();
    const month = String(dt.getMonth() + 1).padStart(2, '0');
    const day = String(dt.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function roundTo(num, decimals) {
    const factor = Math.pow(10, decimals);
    return Math.round(num * factor) / factor;
}
