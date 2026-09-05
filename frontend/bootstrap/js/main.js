/**
 * Smart Traffic Management System - Frontend JavaScript
 */

// API base URLs - dynamic versioned endpoints
const API_BASE_URL = (typeof window !== 'undefined' ? window.location.origin : '') + '/api/v1';
const AUTH_API_URL = `${API_BASE_URL}/auth`;

function getAuthHeaders(headers = {}) {
    const token = localStorage.getItem('token') || localStorage.getItem('stms_token');
    const authHeaders = { ...headers };
    if (token) {
        authHeaders['Authorization'] = `Bearer ${token}`;
    }
    return authHeaders;
}

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication status
    updateAuthUI();
    
    // Setup logout functionality if the button exists
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
    // Initialize elements
    const uploadBtn = document.getElementById('upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const previewImage = document.getElementById('preview-image');
    const optimizeBtn = document.getElementById('optimize-btn');
    const insightsBtn = document.getElementById('insights-btn');
    
    // Stats elements
    const vehicleCount = document.getElementById('vehicle-count');
    const pedestrianCount = document.getElementById('pedestrian-count');
    const weatherCondition = document.getElementById('weather-condition');
    const congestionLevel = document.getElementById('congestion-level');
    const potholeCount = document.getElementById('pothole-count');
    const trafficSigns = document.getElementById('traffic-signs');
    const railwayCrossingStatus = document.getElementById('railway-crossing-status');
    const detectionResults = document.getElementById('detection-results');
    const signalTimings = document.getElementById('signal-timings');
    const aiInsights = document.getElementById('ai-insights');
    
    // Event Listeners
    uploadBtn.addEventListener('click', () => {
        fileUpload.click();
    });
    
    fileUpload.addEventListener('change', handleFileUpload);
    optimizeBtn.addEventListener('click', optimizeSignals);
    insightsBtn.addEventListener('click', generateInsights);
    
    /**
     * Handle file upload for processing
     */
    async function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        // Show loading state
        setLoading(true);
        
        try {
            // Process the image with all detection endpoints
            await Promise.all([
                processObjectDetection(file),
                processPotholeDetection(file),
                processWeatherDetection(file),
                processTrafficSignDetection(file),
                processRailwayCrossingDetection(file)
            ]);
            
            // Update status
            updateDetectionStatus('Image processed successfully!', 'success');
            
        } catch (error) {
            console.error('Error processing image:', error);
            updateDetectionStatus('Error processing image. Please try again.', 'error');
        } finally {
            setLoading(false);
        }
    }
    
    /**
     * Process image with object detection
     */
    async function processObjectDetection(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/detect/objects`, {
                method: 'POST',
                headers: getAuthHeaders(),
                credentials: 'include',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update stats
                vehicleCount.textContent = data.vehicle_count;
                pedestrianCount.textContent = data.pedestrian_count;
                
                // Update congestion level
                const congestion = calculateCongestion(data.vehicle_count);
                congestionLevel.textContent = congestion.level;
                congestionLevel.style.color = congestion.color;
                
                // Display detection results
                displayDetections(data.objects);
                
                return data;
            } else {
                throw new Error('Object detection failed');
            }
        } catch (error) {
            console.error('Object detection error:', error);
            throw error;
        }
    }
    
    /**
     * Process image with pothole detection
     */
    async function processPotholeDetection(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/detect/potholes`, {
                method: 'POST',
                headers: getAuthHeaders(),
                credentials: 'include',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update stats
                potholeCount.textContent = data.count;
                
                return data;
            } else {
                throw new Error('Pothole detection failed');
            }
        } catch (error) {
            console.error('Pothole detection error:', error);
            throw error;
        }
    }
    
    /**
     * Process image with weather detection
     */
    async function processWeatherDetection(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/detect/weather`, {
                method: 'POST',
                headers: getAuthHeaders(),
                credentials: 'include',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update stats
                weatherCondition.textContent = capitalizeFirstLetter(data.condition);
                
                // Set weather color
                weatherCondition.style.color = getWeatherColor(data.condition);
                
                return data;
            } else {
                throw new Error('Weather detection failed');
            }
        } catch (error) {
            console.error('Weather detection error:', error);
            throw error;
        }
    }
    
    /**
     * Process image with traffic sign detection
     */
    async function processTrafficSignDetection(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/detect/traffic-signs`, {
                method: 'POST',
                headers: getAuthHeaders(),
                credentials: 'include',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update traffic signs display
                displayTrafficSigns(data.signs);
                
                return data;
            } else {
                throw new Error('Traffic sign detection failed');
            }
        } catch (error) {
            console.error('Traffic sign detection error:', error);
            throw error;
        }
    }
    
    /**
     * Process image with railway crossing detection
     */
    async function processRailwayCrossingDetection(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE_URL}/detect/railway-crossing`, {
                method: 'POST',
                headers: getAuthHeaders(),
                credentials: 'include',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update railway crossing status
                updateRailwayCrossingStatus(data);
                
                return data;
            } else {
                throw new Error('Railway crossing detection failed');
            }
        } catch (error) {
            console.error('Railway crossing detection error:', error);
            throw error;
        }
    }
    
    /**
     * Optimize traffic signals
     */
    async function optimizeSignals() {
        try {
            setLoading(true);
            
            const response = await fetch(`${API_BASE_URL}/optimize/signals`, {
                method: 'POST',
                headers: getAuthHeaders({
                    'Content-Type': 'application/json',
                }),
                credentials: 'include',
                body: JSON.stringify({
                    junction_id: "junction_1",
                    traffic_data: {
                        vehicle_count: parseInt(vehicleCount.textContent) || 0,
                        pedestrian_count: parseInt(pedestrianCount.textContent) || 0
                    },
                    weather_data: {
                        condition: weatherCondition.textContent.toLowerCase() || 'clear',
                        confidence: 1.0
                    }
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Display optimized signal timings
                displaySignalTimings(data.optimized_timings);
                
                // Update congestion level
                const congestion = {
                    level: data.congestion_level < 0.3 ? 'Low' : 
                           data.congestion_level < 0.7 ? 'Medium' : 'High',
                    color: data.congestion_level < 0.3 ? '#34a853' : 
                           data.congestion_level < 0.7 ? '#fbbc05' : '#ea4335'
                };
                
                congestionLevel.textContent = congestion.level;
                congestionLevel.style.color = congestion.color;
                
                updateDetectionStatus('Signal timings optimized!', 'success');
            } else {
                throw new Error('Signal optimization failed');
            }
        } catch (error) {
            console.error('Optimization error:', error);
            updateDetectionStatus('Error optimizing signals. Please try again.', 'error');
        } finally {
            setLoading(false);
        }
    }
    
    /**
     * Generate traffic insights using LLM
     */
    async function generateInsights() {
        try {
            setLoading(true);
            
            // Collect current traffic data
            const trafficData = {
                vehicle_count: parseInt(vehicleCount.textContent) || 0,
                pedestrian_count: parseInt(pedestrianCount.textContent) || 0,
                congestion_level: calculateCongestionValue(congestionLevel.textContent),
                avg_waiting: 30 // Example default value
            };
            
            // Collect weather data
            const weatherData = {
                condition: weatherCondition.textContent.toLowerCase(),
                impact_factor: getWeatherImpactFactor(weatherCondition.textContent.toLowerCase())
            };
            
            const prompt = `Traffic Analysis for junction_1: vehicles=${trafficData.vehicle_count}, pedestrians=${trafficData.pedestrian_count}, weather=${weatherData.condition}`;
            const response = await fetch(`${API_BASE_URL}/generate/insights`, {
                method: 'POST',
                headers: getAuthHeaders({
                    'Content-Type': 'application/json',
                }),
                credentials: 'include',
                body: JSON.stringify({
                    prompt: prompt
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Display insights
                displayInsights(data);
                
                updateDetectionStatus('Traffic insights generated!', 'success');
            } else {
                throw new Error('Insights generation failed');
            }
        } catch (error) {
            console.error('Insights error:', error);
            updateDetectionStatus('Error generating insights. Please try again.', 'error');
        } finally {
            setLoading(false);
        }
    }
    
    /**
     * Display object detections
     */
    function displayDetections(objects) {
        if (!objects || objects.length === 0) {
            detectionResults.innerHTML = '<p>No objects detected.</p>';
            return;
        }
        
        // Group objects by class
        const grouped = objects.reduce((acc, obj) => {
            if (!acc[obj.class]) {
                acc[obj.class] = [];
            }
            acc[obj.class].push(obj);
            return acc;
        }, {});
        
        let html = '';
        
        // Create detection items
        Object.entries(grouped).forEach(([cls, items]) => {
            const type = getObjectType(cls);
            html += `
                <div class="detection-item">
                    <div>
                        <span class="detection-type type-${type}">${cls}</span>
                        <span class="ms-2">${items.length} detected</span>
                    </div>
                    <div>
                        <span class="badge bg-info">${Math.round(items[0].confidence * 100)}% conf.</span>
                    </div>
                </div>
            `;
        });
        
        detectionResults.innerHTML = html;
    }
    
    /**
     * Display traffic signs
     */
    function displayTrafficSigns(signs) {
        if (!signs || signs.length === 0) {
            trafficSigns.innerHTML = '<p>No traffic signs detected.</p>';
            return;
        }
        
        let html = '';
        
        signs.forEach(sign => {
            html += `
                <div class="mb-2">
                    <span class="detection-type type-sign">${formatSignName(sign.class)}</span>
                    <span class="ms-2 badge bg-info">${Math.round(sign.confidence * 100)}% conf.</span>
                </div>
            `;
        });
        
        trafficSigns.innerHTML = html;
    }
    
    /**
     * Update railway crossing status
     */
    function updateRailwayCrossingStatus(data) {
        let statusText = 'No railway crossings detected';
        let statusClass = 'text-success';
        
        if (data.has_crossing) {
            statusText = data.train_present ? 
                'WARNING: Active railway crossing with train present!' : 
                'Railway crossing detected (no train present)';
                
            statusClass = data.train_present ? 'text-danger' : 'text-warning';
        }
        
        railwayCrossingStatus.textContent = statusText;
        railwayCrossingStatus.className = statusClass;
    }
    
    /**
     * Display signal timings
     */
    function displaySignalTimings(timings) {
        if (!timings) {
            signalTimings.innerHTML = '<p>No signal timing data available.</p>';
            return;
        }
        
        let html = '';
        
        // Display each direction's timing
        Object.entries(timings).forEach(([direction, timing]) => {
            html += `
                <div class="signal-timing">
                    <div>
                        <strong>${formatDirection(direction)}</strong>
                    </div>
                    <div>
                        <span class="signal-light red"></span>
                        <span class="signal-value">${timing.red}s</span>
                        <span class="signal-light yellow ms-2"></span>
                        <span class="signal-value">${timing.yellow}s</span>
                        <span class="signal-light green ms-2"></span>
                        <span class="signal-value">${timing.green}s</span>
                    </div>
                </div>
            `;
        });
        
        signalTimings.innerHTML = html;
    }
    
    /**
     * Display insights
     */
    function displayInsights(data) {
        if (!data || !data.insight_text) {
            aiInsights.innerHTML = '<p>No insights available.</p>';
            return;
        }
        
        let html = `
            <div class="mb-3">
                <h5>Analysis:</h5>
                <p>${data.insight_text}</p>
            </div>
            <div>
                <h5>Recommendations:</h5>
            </div>
        `;
        
        // Add recommendations
        data.recommendations.forEach(rec => {
            html += `<div class="recommendation mb-2">${rec}</div>`;
        });
        
        aiInsights.innerHTML = html;
    }
    
    /**
     * Set loading state
     */
    function setLoading(isLoading) {
        document.querySelectorAll('.btn').forEach(btn => {
            btn.disabled = isLoading;
            if (isLoading) {
                btn.innerHTML = '<span class="loading me-2"></span>Processing...';
            } else {
                // Restore original button text
                if (btn === uploadBtn) btn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload Image/Video';
                else if (btn === optimizeBtn) btn.innerHTML = 'Optimize Signals';
                else if (btn === insightsBtn) btn.innerHTML = 'Generate Insights';
            }
        });
    }
    
    /**
     * Update detection status
     */
    function updateDetectionStatus(message, type) {
        const statusDiv = document.createElement('div');
        statusDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} mt-3 alert-dismissible fade show`;
        statusDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to dashboard
        document.querySelector('#dashboard').appendChild(statusDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            statusDiv.remove();
        }, 5000);
    }
    
    // Helper functions
    
    /**
     * Calculate congestion based on vehicle count
     */
    function calculateCongestion(count) {
        if (count < 5) {
            return { level: 'Low', color: '#34a853' };
        } else if (count < 15) {
            return { level: 'Medium', color: '#fbbc05' };
        } else {
            return { level: 'High', color: '#ea4335' };
        }
    }
    
    /**
     * Calculate congestion value from text
     */
    function calculateCongestionValue(text) {
        switch (text.toLowerCase()) {
            case 'low': return 0.2;
            case 'medium': return 0.5;
            case 'high': return 0.8;
            default: return 0.5;
        }
    }
    
    /**
     * Get color for weather condition
     */
    function getWeatherColor(condition) {
        switch (condition.toLowerCase()) {
            case 'clear': return '#34a853';
            case 'cloudy': return '#5f6368';
            case 'rain': return '#4285f4';
            case 'snow': return '#8521d4';
            case 'fog': return '#9aa0a6';
            case 'haze': return '#f29900';
            case 'night': return '#202124';
            default: return '#000';
        }
    }
    
    /**
     * Get impact factor for weather condition
     */
    function getWeatherImpactFactor(condition) {
        switch (condition.toLowerCase()) {
            case 'clear': return 0.1;
            case 'cloudy': return 0.2;
            case 'rain': return 0.6;
            case 'snow': return 0.8;
            case 'fog': return 0.7;
            case 'haze': return 0.3;
            case 'night': return 0.4;
            default: return 0.1;
        }
    }
    
    /**
     * Get object type for styling
     */
    function getObjectType(cls) {
        cls = cls.toLowerCase();
        if (['car', 'truck', 'bus', 'motorbike', 'bicycle'].includes(cls)) {
            return 'vehicle';
        } else if (cls === 'person') {
            return 'pedestrian';
        } else if (['pothole', 'damage', 'crack'].includes(cls)) {
            return 'pothole';
        } else if (['sign', 'hump', 'pedestrian_crossing'].includes(cls)) {
            return 'sign';
        } else if (['train', 'railway', 'railroad', 'crossing'].includes(cls)) {
            return 'railway';
        }
        return 'vehicle';
    }
    
    /**
     * Format sign name for display
     */
    function formatSignName(name) {
        return name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    /**
     * Format direction for display
     */
    function formatDirection(dir) {
        return dir.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    /**
     * Capitalize first letter
     */
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    /**
     * Update authentication UI based on login status
     */
    function updateAuthUI() {
        // Check if user is authenticated
        const isLoggedIn = isAuthenticated();
        const loginLink = document.getElementById('login-link');
        const logoutBtn = document.getElementById('logout-btn');
        
        if (loginLink && logoutBtn) {
            if (isLoggedIn) {
                loginLink.classList.add('d-none');
                logoutBtn.classList.remove('d-none');
            } else {
                loginLink.classList.remove('d-none');
                logoutBtn.classList.add('d-none');
            }
        }
        
        // If this is a restricted page and user is not logged in, redirect to login
        if (!isLoggedIn && isRestrictedPage()) {
            window.location.href = 'login.html';
        }
    }
    
    /**
     * Check if current page is restricted (requires login)
     */
    function isRestrictedPage() {
        // List of pages that require authentication
        const restrictedPages = ['dashboard.html', 'profile.html'];
        
        // Get current page filename
        const currentPage = window.location.pathname.split('/').pop();
        
        return restrictedPages.includes(currentPage);
    }
});