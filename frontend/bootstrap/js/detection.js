/**
 * Frontend detection module for Smart Traffic Management System
 * Handles traffic image uploads and analysis display
 */

// Import auth for token
import { getAuthToken } from './auth.js';

// Get base URL from config
let apiBaseUrl = '';

// Import configuration if available
try {
    const config = await import('../config.js');
    apiBaseUrl = config.API_BASE_URL || '';
} catch (err) {
    console.warn('Failed to load config.js, using default API base URL');
    // Fallback to default
    apiBaseUrl = window.location.origin;
}

document.addEventListener('DOMContentLoaded', function() {
    setupDetectionForms();
    setupTabSwitch();
});

/**
 * Setup detection forms and image upload handlers
 */
function setupDetectionForms() {
    // Traffic detection form
    const trafficForm = document.getElementById('traffic-detection-form');
    if (trafficForm) {
        trafficForm.addEventListener('submit', handleTrafficDetection);
    }
    
    // Pothole detection form
    const potholeForm = document.getElementById('pothole-detection-form');
    if (potholeForm) {
        potholeForm.addEventListener('submit', handlePotholeDetection);
    }
    
    // Weather detection form
    const weatherForm = document.getElementById('weather-detection-form');
    if (weatherForm) {
        weatherForm.addEventListener('submit', handleWeatherDetection);
    }
    
    // Traffic sign detection form
    const trafficSignForm = document.getElementById('traffic-sign-detection-form');
    if (trafficSignForm) {
        trafficSignForm.addEventListener('submit', handleTrafficSignDetection);
    }
    
    // Railway crossing detection form
    const railwayForm = document.getElementById('railway-crossing-detection-form');
    if (railwayForm) {
        railwayForm.addEventListener('submit', handleRailwayDetection);
    }
    
    // Setup file input preview for all forms
    setupImagePreviews();
}

/**
 * Setup image preview for file inputs
 */
function setupImagePreviews() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Check if file is an image
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
            
            // Find the closest image preview element
            const form = input.closest('form');
            const preview = form.querySelector('.image-preview');
            
            if (preview) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                
                reader.readAsDataURL(file);
            }
        });
    });
}

/**
 * Handle traffic detection form submission
 */
async function handleTrafficDetection(event) {
    event.preventDefault();
    await processDetection(event.target, '/detect/objects', renderTrafficResults);
}

/**
 * Handle pothole detection form submission
 */
async function handlePotholeDetection(event) {
    event.preventDefault();
    await processDetection(event.target, '/detect/potholes', renderPotholeResults);
}

/**
 * Handle weather detection form submission
 */
async function handleWeatherDetection(event) {
    event.preventDefault();
    await processDetection(event.target, '/detect/weather', renderWeatherResults);
}

/**
 * Handle traffic sign detection form submission
 */
async function handleTrafficSignDetection(event) {
    event.preventDefault();
    await processDetection(event.target, '/detect/traffic-signs', renderTrafficSignResults);
}

/**
 * Handle railway crossing detection form submission
 */
async function handleRailwayDetection(event) {
    event.preventDefault();
    await processDetection(event.target, '/detect/railway-crossing', renderRailwayResults);
}

/**
 * Process image upload and detection
 * @param {HTMLFormElement} form - The form element
 * @param {string} endpoint - API endpoint for detection
 * @param {Function} renderFunction - Function to render results
 */
async function processDetection(form, endpoint, renderFunction) {
    const fileInput = form.querySelector('input[type="file"]');
    const file = fileInput.files[0];
    
    if (!file) {
        showError(form, 'Please select an image file');
        return;
    }
    
    // Show loading state
    const resultContainer = form.querySelector('.results-container');
    const loadingElement = form.querySelector('.loading');
    const errorElement = form.querySelector('.error-message');
    
    if (resultContainer) resultContainer.innerHTML = '';
    if (loadingElement) loadingElement.style.display = 'block';
    if (errorElement) errorElement.style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }
        
        // Add debug logging
        console.log(`Sending request to: ${apiBaseUrl}${endpoint}`);
        
        const response = await fetch(`${apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (loadingElement) loadingElement.style.display = 'none';
        
        if (response.ok) {
            const data = await response.json();
            
            // Render results
            if (renderFunction && resultContainer) {
                renderFunction(data, resultContainer);
            }
        } else {
            // Handle error response
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Error: ${response.status} ${response.statusText}`;
            showError(form, errorMessage);
            console.error('API Error:', errorMessage);
        }
    } catch (err) {
        console.error('Detection error:', err);
        showError(form, `Error processing image: ${err.message || 'Unknown error'}`);
        
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

/**
 * Show error message in form
 */
function showError(form, message) {
    const errorElement = form.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
    
    const loadingElement = form.querySelector('.loading');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

/**
 * Render traffic detection results
 */
function renderTrafficResults(data, container) {
    const vehicleCount = data.vehicle_count || 0;
    const pedestrianCount = data.pedestrian_count || 0;
    
    let html = `
        <h3>Detection Results</h3>
        <div class="result-summary">
            <div class="stat-card">
                <span class="stat-value">${vehicleCount}</span>
                <span class="stat-label">Vehicles</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">${pedestrianCount}</span>
                <span class="stat-label">Pedestrians</span>
            </div>
        </div>
    `;
    
    if (data.objects && data.objects.length > 0) {
        html += '<h4>Detected Objects</h4><ul class="detection-list">';
        
        data.objects.forEach(obj => {
            html += `
                <li class="detection-item">
                    <span class="detection-class">${obj.class}</span>
                    <span class="detection-confidence">Confidence: ${(obj.confidence * 100).toFixed(1)}%</span>
                </li>
            `;
        });
        
        html += '</ul>';
    }
    
    container.innerHTML = html;
}

/**
 * Render pothole detection results
 */
function renderPotholeResults(data, container) {
    const potholeCount = data.count || 0;
    
    let html = `
        <h3>Pothole Detection Results</h3>
        <div class="result-summary">
            <div class="stat-card">
                <span class="stat-value">${potholeCount}</span>
                <span class="stat-label">Potholes</span>
            </div>
        </div>
    `;
    
    if (data.potholes && data.potholes.length > 0) {
        html += '<h4>Detected Potholes</h4><ul class="detection-list">';
        
        data.potholes.forEach(pothole => {
            html += `
                <li class="detection-item">
                    <span class="detection-class">Pothole</span>
                    <span class="detection-confidence">Severity: ${pothole.severity || 'Medium'}</span>
                    <span class="detection-confidence">Confidence: ${(pothole.confidence * 100).toFixed(1)}%</span>
                </li>
            `;
        });
        
        html += '</ul>';
    }
    
    container.innerHTML = html;
}

/**
 * Render weather detection results
 */
function renderWeatherResults(data, container) {
    const condition = data.condition || 'Unknown';
    const confidence = data.confidence || 0;
    const impactFactor = data.impact_factor || 0;
    
    let html = `
        <h3>Weather Analysis Results</h3>
        <div class="result-summary">
            <div class="stat-card">
                <span class="stat-value">${condition}</span>
                <span class="stat-label">Condition</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">${(confidence * 100).toFixed(1)}%</span>
                <span class="stat-label">Confidence</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">${impactFactor.toFixed(2)}</span>
                <span class="stat-label">Traffic Impact</span>
            </div>
        </div>
    `;
    
    if (data.temperature || data.humidity) {
        html += '<h4>Weather Metrics</h4><div class="weather-metrics">';
        
        if (data.temperature) {
            html += `<div class="metric"><span>Temperature:</span> ${data.temperature}°C</div>`;
        }
        
        if (data.humidity) {
            html += `<div class="metric"><span>Humidity:</span> ${data.humidity}%</div>`;
        }
        
        html += '</div>';
    }
    
    container.innerHTML = html;
}

/**
 * Render traffic sign detection results
 */
function renderTrafficSignResults(data, container) {
    const signCount = data.count || 0;
    
    let html = `
        <h3>Traffic Sign Detection Results</h3>
        <div class="result-summary">
            <div class="stat-card">
                <span class="stat-value">${signCount}</span>
                <span class="stat-label">Signs</span>
            </div>
        </div>
    `;
    
    if (data.signs && data.signs.length > 0) {
        html += '<h4>Detected Signs</h4><ul class="detection-list">';
        
        data.signs.forEach(sign => {
            html += `
                <li class="detection-item">
                    <span class="detection-class">${sign.class || sign.type || 'Unknown'}</span>
                    <span class="detection-confidence">Confidence: ${(sign.confidence * 100).toFixed(1)}%</span>
                </li>
            `;
        });
        
        html += '</ul>';
    }
    
    container.innerHTML = html;
}

/**
 * Render railway crossing detection results
 */
function renderRailwayResults(data, container) {
    const hasCrossing = data.has_crossing;
    const trainPresent = data.train_present;
    
    let html = `
        <h3>Railway Crossing Detection</h3>
        <div class="result-summary">
            <div class="stat-card ${hasCrossing ? 'alert' : ''}">
                <span class="stat-value">${hasCrossing ? 'Yes' : 'No'}</span>
                <span class="stat-label">Crossing Detected</span>
            </div>
            <div class="stat-card ${trainPresent ? 'warning' : ''}">
                <span class="stat-value">${trainPresent ? 'Present' : 'None'}</span>
                <span class="stat-label">Train</span>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Setup tab switching functionality
 */
function setupTabSwitch() {
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            const activeContent = document.getElementById(tabId);
            if (activeContent) {
                activeContent.classList.add('active');
            }
        });
    });
}