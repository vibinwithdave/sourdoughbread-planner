/**
 * Sourdough Bread Planner - Frontend Application
 * Handles form interaction, API calls, and results rendering.
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeForm();
    attachEventListeners();
});

// --- Initialization ---

function initializeForm() {
    // Set current local time
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    const minutesStr = minutes < 10 ? '0' + minutes : String(minutes);
    const currentTime = `${hours}:${minutesStr} ${ampm}`;

    document.getElementById('start_time').value = currentTime;
    document.getElementById('currentTimeHint').textContent = `Current time: ${currentTime}`;

    // Update bulk estimate on load
    updateBulkEstimate();

    // Update starter preview on load
    updateStarterPreview();
}

function attachEventListeners() {
    // Form submission
    document.getElementById('scheduleForm').addEventListener('submit', handleFormSubmit);

    // Temperature change -> update bulk estimate
    document.getElementById('temperature_f').addEventListener('input', updateBulkEstimate);

    // Starter-related inputs -> update preview
    document.getElementById('existing_starter_amount').addEventListener('input', updateStarterPreview);
    document.getElementById('feeding_ratio').addEventListener('change', updateStarterPreview);
    document.getElementById('total_flour_weight').addEventListener('input', updateStarterPreview);
    document.getElementById('starter_percent').addEventListener('input', updateStarterPreview);
}

// --- Live Updates ---

function updateBulkEstimate() {
    const temp = parseFloat(document.getElementById('temperature_f').value) || 70;
    const hours = estimateBulkHours(temp);
    document.getElementById('bulkEstimate').textContent = `~${hours} hours bulk fermentation`;
}

function estimateBulkHours(tempF) {
    // Client-side estimation matching the backend logic
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
    const totalFlour = parseFloat(document.getElementById('total_flour_weight').value) || 500;
    const starterPercent = parseFloat(document.getElementById('starter_percent').value) || 20;

    // Parse ratio
    const parts = ratio.split(':').map(Number);
    const flourParts = parts[1];
    const waterParts = parts[2];

    const totalAfterFeeding = existingStarter + (existingStarter * flourParts) + (existingStarter * waterParts);
    const starterNeeded = totalFlour * (starterPercent / 100);
    const remaining = Math.max(0, totalAfterFeeding - starterNeeded);

    let statusText = '';
    if (totalAfterFeeding >= starterNeeded) {
        statusText = `Feeding ${existingStarter}g at ${ratio} produces ${Math.round(totalAfterFeeding)}g. ` +
            `Recipe needs ${Math.round(starterNeeded)}g, leaving ${Math.round(remaining)}g for future bakes.`;
    } else {
        statusText = `Warning: Feeding ${existingStarter}g at ${ratio} only produces ${Math.round(totalAfterFeeding)}g, ` +
            `but recipe needs ${Math.round(starterNeeded)}g. Increase starter amount or change ratio.`;
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
    const form = document.getElementById('scheduleForm');

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

    return {
        total_flour_weight: parseFloat(document.getElementById('total_flour_weight').value),
        hydration: parseFloat(document.getElementById('hydration').value),
        salt_percent: parseFloat(document.getElementById('salt_percent').value),
        starter_percent: parseFloat(document.getElementById('starter_percent').value),
        existing_starter_amount: parseFloat(document.getElementById('existing_starter_amount').value),
        feeding_ratio: document.getElementById('feeding_ratio').value,
        start_time: document.getElementById('start_time').value,
        temperature_f: parseFloat(document.getElementById('temperature_f').value),
        cold_proof_hours: parseFloat(document.getElementById('cold_proof_hours').value),
        flour_type: document.getElementById('flour_type').value,
        enabled_steps: enabledSteps
    };
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

    // Starter Feeding Panel
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
                : 'Insufficient! Increase starter amount or change ratio'}
        </div>
    `;

    // Main Dough Panel
    document.getElementById('mainDoughResults').innerHTML = `
        <div class="ingredient-row">
            <span class="label">Active Starter</span>
            <span class="value">${ingredients.starter_for_recipe}g</span>
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

    // Totals Panel
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
    // Timeline info badges
    document.getElementById('timelineInfo').innerHTML = `
        <span class="timeline-badge"><strong>${settings.temperature_f}°F</strong> kitchen</span>
        <span class="timeline-badge"><strong>~${settings.bulk_fermentation_estimate}h</strong> bulk ferment</span>
        <span class="timeline-badge"><strong>${settings.cold_proof_hours}h</strong> cold proof</span>
        <span class="timeline-badge"><strong>${settings.hydration}%</strong> hydration</span>
        <span class="timeline-badge"><strong>${settings.feeding_ratio}</strong> feed ratio</span>
    `;

    // Timeline visual
    let html = '';
    days.forEach(day => {
        html += `<div class="timeline-day">`;
        html += `<div class="timeline-day-header">${day.date}</div>`;
        html += `<div class="timeline-steps">`;

        day.steps.forEach(step => {
            html += `
                <div class="timeline-step" data-category="${step.category}">
                    <div class="step-header">
                        <span class="step-name">${step.name}</span>
                        <span class="step-time">${step.time_display}</span>
                    </div>
                    <div class="step-description">${step.description}</div>
                    <div class="step-visual-cue">${step.visual_cue}</div>
                    ${step.note ? `<div class="step-note">${step.note}</div>` : ''}
                </div>
            `;
        });

        html += `</div></div>`;
    });

    document.getElementById('timelineVisual').innerHTML = html;
}
