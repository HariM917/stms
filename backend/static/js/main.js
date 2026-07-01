
document.addEventListener('DOMContentLoaded', function() {
    // API endpoint base URL - change this if your backend is on a different port
    const API_URL = 'http://localhost:8000';
    
    // Mock API calls for demo purposes
    function mockApiCall(endpoint, data, callback) {
        console.log(`Mock API call to ${endpoint} with data:`, data);
        
        setTimeout(() => {
            let response;
            
            switch(endpoint) {
                case '/detect/traffic':
                    response = {
                        "detections": [
                            {"class": "car", "confidence": 0.95, "box": [10, 10, 100, 100]},
                            {"class": "person", "confidence": 0.87, "box": [200, 200, 250, 300]},
                            {"class": "motorcycle", "confidence": 0.82, "box": [300, 150, 350, 200]}
                        ],
                        "density_analysis": {
                            "vehicle_count": 15,
                            "density_ratio": 0.23,
                            "congestion_level": 2
                        }
                    };
                    break;
                    
                case '/detect/potholes':
                    response = {
                        "count": 3,
                        "severity": "medium",
                        "locations": [
                            {"box": [120, 230, 180, 290], "confidence": 0.88},
                            {"box": [350, 400, 420, 470], "confidence": 0.92},
                            {"box": [500, 300, 550, 350], "confidence": 0.78}
                        ]
                    };
                    break;
                    
                case '/detect/traffic_signs':
                    response = {
                        "sign_detections": [
                            {"class": "hump", "confidence": 0.91},
                            {"class": "pedestrian_crossing", "confidence": 0.85}
                        ]
                    };
                    break;
                    
                case '/detect/weather':
                    response = {
                        "condition": "clear",
                        "confidence": 0.93,
                        "impact_factor": 0.95
                    };
                    break;
                    
                case '/insights/generate':
                    response = {
                        "insight_text": "Moderate traffic congestion detected. Current vehicle count is within typical range for this time. Consider extending green light duration at the main intersection by 10 seconds. Address pothole repairs to improve traffic flow efficiency.",
                        "confidence": 0.87
                    };
                    break;
                    
                default:
                    response = { "error": "Unknown endpoint" };
            }
            
            callback(response);
        }, 1500);
    }
    
    // Traffic Analysis
    document.getElementById('analyzeTraffic').addEventListener('click', function() {
        const fileInput = document.getElementById('trafficImage');
        if (!fileInput.files.length) {
            alert('Please select an image first');
            return;
        }
        
        const resultsDiv = document.getElementById('trafficResults');
        resultsDiv.innerHTML = '<p>Analyzing traffic...</p>';
        
        // Create form data with the file
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        // Make API call (mock for demo)
        mockApiCall('/detect/traffic', formData, function(data) {
            let html = `
                <h3>Traffic Analysis Results:</h3>
                <p>Vehicles detected: ${data.density_analysis.vehicle_count}</p>
                <p>Congestion level: ${['Low', 'Moderate', 'High', 'Very High'][data.density_analysis.congestion_level]}</p>
                <p>Density ratio: ${data.density_analysis.density_ratio.toFixed(2)}</p>
                <h4>Detected Objects:</h4>
                <ul>
            `;
            
            data.detections.forEach(obj => {
                html += `<li>${obj.class} (confidence: ${obj.confidence.toFixed(2)})</li>`;
            });
            
            html += '</ul>';
            resultsDiv.innerHTML = html;
        });
    });
    
    // Road Condition Analysis
    document.getElementById('analyzeRoad').addEventListener('click', function() {
        const fileInput = document.getElementById('roadImage');
        if (!fileInput.files.length) {
            alert('Please select an image first');
            return;
        }
        
        const resultsDiv = document.getElementById('roadResults');
        resultsDiv.innerHTML = '<p>Analyzing road condition...</p>';
        
        // Create form data with the file
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        // Make API call (mock for demo)
        mockApiCall('/detect/potholes', formData, function(data) {
            resultsDiv.innerHTML = `
                <h3>Road Condition Results:</h3>
                <p>Potholes detected: ${data.count}</p>
                <p>Severity: ${data.severity}</p>
                <p>Confidence: ${data.locations[0].confidence.toFixed(2)}</p>
            `;
        });
    });
    
    // Traffic Sign Detection
    document.getElementById('analyzeSigns').addEventListener('click', function() {
        const fileInput = document.getElementById('signImage');
        if (!fileInput.files.length) {
            alert('Please select an image first');
            return;
        }
        
        const resultsDiv = document.getElementById('signResults');
        resultsDiv.innerHTML = '<p>Analyzing traffic signs...</p>';
        
        // Create form data with the file
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        // Make API call (mock for demo)
        mockApiCall('/detect/traffic_signs', formData, function(data) {
            let html = '<h3>Traffic Sign Detection:</h3>';
            
            if (data.sign_detections && data.sign_detections.length > 0) {
                html += '<ul>';
                data.sign_detections.forEach(sign => {
                    html += `<li>${sign.class} (confidence: ${sign.confidence.toFixed(2)})</li>`;
                });
                html += '</ul>';
            } else {
                html += '<p>No traffic signs detected</p>';
            }
            
            resultsDiv.innerHTML = html;
        });
    });
    
    // Weather Analysis
    document.getElementById('analyzeWeather').addEventListener('click', function() {
        const fileInput = document.getElementById('weatherImage');
        const location = document.getElementById('location').value;
        
        if (!fileInput.files.length && !location) {
            alert('Please select an image or enter a location');
            return;
        }
        
        const resultsDiv = document.getElementById('weatherResults');
        resultsDiv.innerHTML = '<p>Analyzing weather conditions...</p>';
        
        // Create form data
        const formData = new FormData();
        if (fileInput.files.length) {
            formData.append('image', fileInput.files[0]);
        }
        if (location) {
            formData.append('location', location);
        }
        
        // Make API call (mock for demo)
        mockApiCall('/detect/weather', formData, function(data) {
            resultsDiv.innerHTML = `
                <h3>Weather Analysis:</h3>
                <p>Condition: ${data.condition}</p>
                <p>Confidence: ${data.confidence.toFixed(2)}</p>
                <p>Impact on traffic: ${data.impact_factor.toFixed(2)}</p>
            `;
        });
    });
    
    // Generate Insights
    document.getElementById('generateInsights').addEventListener('click', function() {
        const insightsDiv = document.getElementById('insightsContent');
        insightsDiv.innerHTML = '<p>Generating AI insights...</p>';
        
        // Mock data
        const requestData = {
            junction_id: "junction_1",
            time_range: "24h",
            metrics: ["congestion", "wait_time", "road_condition"]
        };
        
        // Make API call (mock for demo)
        mockApiCall('/insights/generate', requestData, function(data) {
            insightsDiv.innerHTML = `
                <h3>Traffic Insights:</h3>
                <p>${data.insight_text}</p>
                <p><em>Confidence: ${data.confidence.toFixed(2)}</em></p>
            `;
        });
    });
});
