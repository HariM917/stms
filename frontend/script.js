const API_BASE_URL = window.location.origin + '/api/v1';
const AUTH_API_URL = window.location.origin + '/api/v1/auth';

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

if (!localStorage.getItem('token')) {
    window.location.href = 'landing.html';
}

document.addEventListener('DOMContentLoaded', () => {

const mockRtoDatabase = {
    "TN07CD1234": { owner: "Rajesh Kumar", address: "123 Anna Salai, Chennai" },
    "DL3CAB5678": { owner: "Priya Sharma", address: "456 Connaught Place, Delhi" },
    "KA01EF9012": { owner: "Amit Patel", address: "789 MG Road, Bengaluru" },
    "MH12GH3456": { owner: "Sunita Reddy", address: "101 JM Road, Pune" },
    "WB02IJ7890": { owner: "Sanjay Bose", address: "212 Esplanade, Kolkata" },
    "OD05KL1234": { owner: "Deepa Mohanty", address: "333 Master Canteen, Bhubaneswar" },
};

const trafficDataSample = {
    "07:00": { cars: 20, twoWheelers: 40, autos: 10, heavy: 2 },  // Early morning
    "08:00": { cars: 60, twoWheelers: 150, autos: 40, heavy: 10 }, // Morning Rush
    "09:00": { cars: 85, twoWheelers: 200, autos: 55, heavy: 15 }, // Peak Morning Rush
    "10:00": { cars: 70, twoWheelers: 180, autos: 50, heavy: 12 },
    "12:00": { cars: 50, twoWheelers: 100, autos: 35, heavy: 8 },  // Mid-day
    "14:00": { cars: 45, twoWheelers: 90, autos: 30, heavy: 7 },
    "17:00": { cars: 75, twoWheelers: 190, autos: 50, heavy: 14 }, // Evening Rush
    "18:00": { cars: 90, twoWheelers: 210, autos: 60, heavy: 18 }, // Peak Evening Rush
    "20:00": { cars: 40, twoWheelers: 80, autos: 25, heavy: 5 },  // Late Evening
    "22:00": { cars: 15, twoWheelers: 30, autos: 10, heavy: 3 },   // Night
};

const systemState = {
    isRunning: true,
    aiFeatures: {
        predictive: true,
        signals: true,
        rerouting: true,
        profile: 'Metro-Dense (Default)'
    },
    nodes: {
        "Master Canteen - Bhubaneswar": { name: "Master Canteen - Bhubaneswar", city: "Bhubaneswar", pos: { top: '68%', left: '75%' }, incidents: 5, neighbors: ["Esplanade - Kolkata"], infrastructure: { power: 'Grid', powerBackup: 'Solar', connectivity: '5G', connectivityFailover: 'Fiber'} },
        "Esplanade - Kolkata": { name: "Esplanade - Kolkata", city: "Kolkata", pos: { top: '64%', left: '83%' }, incidents: 12, neighbors: ["Master Canteen - Bhubaneswar", "Connaught Place - Delhi"], infrastructure: { power: 'Grid', powerBackup: 'Battery', connectivity: 'Fiber', connectivityFailover: '4G'} },
        "MG Road - Bengaluru": { name: "MG Road - Bengaluru", city: "Bengaluru", pos: { top: '82%', left: '55%' }, incidents: 8, neighbors: ["Anna Salai - Chennai", "JM Road - Pune"], infrastructure: { power: 'Grid', powerBackup: 'Solar', connectivity: '5G', connectivityFailover: 'Fiber'} },
        "JM Road - Pune": { name: "JM Road - Pune", city: "Pune", pos: { top: '72%', left: '48%' }, incidents: 3, neighbors: ["MG Road - Bengaluru"], infrastructure: { power: 'Grid', powerBackup: 'Battery', connectivity: 'Fiber', connectivityFailover: '5G'} },
        "Connaught Place - Delhi": { name: "Connaught Place - Delhi", city: "Delhi", pos: { top: '48%', left: '54%' }, incidents: 22, neighbors: ["Esplanade - Kolkata"], infrastructure: { power: 'Grid', powerBackup: 'Diesel Gen', connectivity: '5G', connectivityFailover: 'Fiber'} },
        "Anna Salai - Chennai": { name: "Anna Salai - Chennai", city: "Chennai", pos: { top: '81%', left: '63%' }, incidents: 7, neighbors: ["MG Road - Bengaluru"], infrastructure: { power: 'Grid', powerBackup: 'Solar', connectivity: '5G', connectivityFailover: 'Fiber'} }
    },
    potholes: [{ id: 1, severity: 'major', ts: Date.now() / 1000 - 86400 * 2, repaired: false, node: "Master Canteen - Bhubaneswar" }],
    incidents: [{ id: 1, ts: Date.now() / 1000 - 3600 * 5, node: "Connaught Place - Delhi", type: "collision", desc: "Collision-like overlap detected.", rerouting: 'pending', affectedNodes: [], aiSummary: null }],
    violations: [
        { id: 1, ts: Date.now() / 1000 - 3600 * 2, node: "Connaught Place - Delhi", type: 'Speeding', details: { license: "DL3CAB5678", speed: 65, limit: 40, vehicle: '4-Wheeler' }, challanStatus: 'Pending' },
        { id: 2, ts: Date.now() / 1000 - 3600 * 8, node: "MG Road - Bengaluru", type: 'No Helmet', details: { license: "KA01EF9012", offender: 'Driver' }, challanStatus: 'Paid' },
    ],
    systemAlerts: [],
    coordinationLog: [],
    avg_commute: 0,
    publicTransportOnTime: 94.5,
    predictionData: {},
    lastModelUpdate: new Date(Date.now() - 86400000 * 7), // 7 days ago
    lastSecurityAudit: new Date(Date.now() - 86400000 * 15) // 15 days ago
};

// Initialize node data that is derived
Object.values(systemState.nodes).forEach(node => {
    node.density = 0;
    node.vehicles = 0;
    node.vehicleClasses = {cars: 0, twoWheelers: 0, autos: 0, heavy: 0};
    node.animals = 0;
    node.humans = 0;
    node.signal = 15;
    node.aiRecommendedSignal = 15;
    node.manualOverride = null;
    node.predictedDensity = 0;
    node.isAffected = false;
    node.alertState = 'idle';
    node.lastAlert = 0;
    node.signalStatus = 'Healthy';
    node.speedLimit = { fourWheeler: 50, twoWheeler: 40 };
});

let charts = {};
const MAX_PREDICTION_POINTS = 20;
const ALERT_COOLDOWN = 10000; // 10 seconds

let simulationTime = new Date("2025-09-12T07:00:00");
const SIMULATED_MINUTES_PER_TICK = 5;

const getNodeColorClass = (density) => {
    if (density > 75) return 'bg-density-red';
    if (density > 40) return 'bg-density-orange';
    return 'bg-density-green';
};

const callGeminiAPI = async (prompt, useGrounding = false) => {
    try {
        const response = await fetch(`${API_BASE_URL}/insights`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, useGrounding })
        });
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.insights) {
                return result.insights.join('\n');
            }
        }
        return "Error: Could not retrieve AI insights from server.";
    } catch (error) {
        console.error("API call failed:", error);
        return `Error: Could not connect to the API service. ${error.message}`;
    }
};

const runAiSimulation = () => {
    const now = Date.now();
    Object.values(systemState.nodes).forEach(node => {
        if(node.manualOverride) {
            node.signal = node.manualOverride.duration;
            if(now > node.manualOverride.expiry) node.manualOverride = null;
            return;
        }

         if (systemState.aiFeatures.predictive) {
            const noise = (Math.random() - 0.5) * 10;
            node.predictedDensity = Math.max(0, Math.min(100, node.density + noise));
        }
        if (systemState.aiFeatures.signals) {
            let recommendation = 15;
            if (node.density > 80) recommendation = 45;
            else if (node.density > 60) recommendation = 35;
            else if (node.density > 40) recommendation = 25;
            else if (node.density < 10) recommendation = 10;
            node.aiRecommendedSignal = recommendation;
            node.signal = recommendation;
        }
         if (node.density > 85 && now - node.lastAlert > ALERT_COOLDOWN) {
            node.alertState = 'sending';
            node.lastAlert = now;
            const alert = {
                id: Date.now(),
                ts: now,
                from: node.name,
                to: [],
                type: 'network'
            };
            node.neighbors.forEach(neighborName => {
                const neighborNode = systemState.nodes[neighborName];
                if (neighborNode) {
                    neighborNode.alertState = 'receiving';
                    if(!neighborNode.manualOverride) neighborNode.aiRecommendedSignal += 5; 
                    alert.to.push(neighborName);
                    setTimeout(() => { neighborNode.alertState = 'idle'; }, 4000);
                }
            });
            systemState.coordinationLog.unshift(alert);
            if (systemState.coordinationLog.length > 20) systemState.coordinationLog.pop();
            setTimeout(() => { node.alertState = 'idle'; }, 4000);
        }
    });
     if (systemState.aiFeatures.rerouting) {
        systemState.incidents.forEach(incident => {
            if (incident.rerouting === 'pending') {
                incident.rerouting = 'active';
                systemState.coordinationLog.unshift({ id: Date.now(), ts: Date.now(), type: 'dispatch', to: 'Traffic Police', message: `Dispatch requested for ${incident.type} at ${incident.node}.`});
                systemState.coordinationLog.unshift({ id: Date.now() + 1, ts: Date.now() + 1, type: 'dispatch', to: 'Municipal Corp', message: `Road cleanup crew notified for ${incident.node}.`});
            }
        });
    }
};

const checkForSignalFaults = () => {
    if (Math.random() < 0.01) {
        const healthyNodes = Object.values(systemState.nodes).filter(n => n.signalStatus === 'Healthy');
        if (healthyNodes.length > 0) {
            const nodeToFault = healthyNodes[Math.floor(Math.random() * healthyNodes.length)];
            nodeToFault.signalStatus = 'Faulty';
            const alert = { id: Date.now(), type: 'Signal Fault', node: nodeToFault.name, ts: Date.now(), resolved: false };
            systemState.systemAlerts.unshift(alert);
            setTimeout(() => {
                const alertToResolve = systemState.systemAlerts.find(a => a.id === alert.id);
                if (alertToResolve) {
                    alertToResolve.resolved = true;
                    nodeToFault.signalStatus = 'Healthy';
                }
            }, 60000);
        }
    }
};

const generateRandomViolation = () => {
    if(Math.random() > 0.1) return;
    const nodes = Object.values(systemState.nodes);
    const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
    const type = ['Speeding', 'Red Light', 'No Helmet'][Math.floor(Math.random() * 3)];
    const license = Object.keys(mockRtoDatabase)[Math.floor(Math.random() * Object.keys(mockRtoDatabase).length)];
    let details = { license };
    if (type === 'Speeding') {
        const limit = randomNode.speedLimit.fourWheeler;
        details.speed = limit + Math.floor(Math.random() * 20) + 5;
        details.limit = limit;
    }
    systemState.violations.unshift({ id: Date.now(), ts: Date.now() / 1000, node: randomNode.name, type, details, challanStatus: 'Not Generated' });
};

const updateDashboard = () => {
    if (!systemState.isRunning) return;

    simulationTime.setMinutes(simulationTime.getMinutes() + SIMULATED_MINUTES_PER_TICK);
    if (simulationTime.getHours() >= 23) {
        simulationTime.setHours(7, 0, 0, 0); // Reset to next morning
    }
    document.getElementById('simulation-time').textContent = simulationTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const currentHour = simulationTime.getHours().toString().padStart(2, '0') + ":00";
    const dataForHour = trafficDataSample[currentHour] || trafficDataSample["07:00"];

    let totalDensity = 0, nodeCount = 0;
    let totalVehicleClasses = { cars: 0, twoWheelers: 0, autos: 0, heavy: 0 };

    generateRandomViolation();
    checkForSignalFaults();

    Object.values(systemState.nodes).forEach(node => {
        // Apply dataset values with slight random variation
        Object.keys(node.vehicleClasses).forEach(key => {
            const baseValue = dataForHour[key] || 0;
            const variation = Math.floor(baseValue * 0.1 * (Math.random() - 0.5)); // +/- 10% noise
            node.vehicleClasses[key] = Math.max(0, baseValue + variation);
        });
        
        node.vehicles = Object.values(node.vehicleClasses).reduce((a, b) => a + b, 0);
        Object.keys(totalVehicleClasses).forEach(k => totalVehicleClasses[k] += node.vehicleClasses[k]);
        
        // Density is based on total vehicles, not just classes to keep it simple
        node.density = Math.min(100, Math.floor(node.vehicles / 4)); // Adjusted density calculation
        totalDensity += node.density;
        nodeCount++;
    });
    
    const avgDensity = totalDensity / nodeCount;
    systemState.avg_commute = (10 + avgDensity * 0.4).toFixed(1);
    systemState.publicTransportOnTime = (98 - avgDensity * 0.15).toFixed(1);
    systemState.totalVehicleClasses = totalVehicleClasses;

    runAiSimulation();

    updateHeaderStats();
    renderMapNodes();
    renderSystemAlerts();
    renderNodesList();
    renderViolationsList();
    renderCoordinationLog();
    renderPotholesList();
    renderIncidentsList();
    updateCharts();
};

const setupTabs = () => {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('[id^="tab-content-"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.id.replace('btn', 'content');
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            tabContents.forEach(content => content.classList.toggle('hidden', content.id !== targetId));
        });
    });
};

const updateHeaderStats = () => {
    document.getElementById('avg-commute').textContent = `${systemState.avg_commute} mins`;
    document.getElementById('public-transport-kpi').textContent = `${systemState.publicTransportOnTime}%`;
    const oneDayAgo = Date.now() / 1000 - 86400;
    document.getElementById('total-violations').textContent = systemState.violations.filter(v => v.ts > oneDayAgo).length;
    document.getElementById('unresolved-potholes').textContent = systemState.potholes.filter(p => !p.repaired).length;
    document.getElementById('system-alerts-count').textContent = systemState.systemAlerts.filter(a => !a.resolved).length;
};

const renderMapNodes = () => {
    const mapContainer = document.querySelector('.map-container');
    mapContainer.innerHTML = '';
    const allNodes = {...systemState.nodes, "Nagpur (Phase 2)": { name: "Nagpur (Phase 2)", city: "Nagpur", pos: { top: '60%', left: '58%' } } };
    Object.values(allNodes).forEach(node => {
        const colorClass = node.density ? getNodeColorClass(node.density) : '';
        const isFaulty = node.signalStatus === 'Faulty';
        const isUpcoming = !node.density;
        const nodeEl = document.createElement('div');
        nodeEl.className = `map-node ${colorClass} ${node.isAffected ? 'affected' : ''} ${isFaulty ? 'faulty' : ''} ${isUpcoming ? 'upcoming' : ''}`;
        nodeEl.style.top = node.pos.top;
        nodeEl.style.left = node.pos.left;
        nodeEl.dataset.nodeName = node.name;
        nodeEl.innerHTML = `<div class="map-node-label">${node.name}</div>`;
        if(!isUpcoming) nodeEl.addEventListener('click', () => openModal(node.name));
        mapContainer.appendChild(nodeEl);
    });
};

const renderSystemAlerts = () => {
    const panel = document.getElementById('system-alerts-panel');
    const activeAlerts = systemState.systemAlerts.filter(a => !a.resolved);
    if(activeAlerts.length === 0) {
        panel.innerHTML = ''; return;
    }
    panel.innerHTML = `<h3 class="font-semibold mb-2 text-slate-800 px-1">System Alerts</h3><div class="space-y-2">${activeAlerts.map(alert => `
            <div class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800 p-3 rounded-lg text-sm flex items-center gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <div>
                    <p class="font-bold">${alert.type}: ${alert.node}</p>
                    <p class="text-xs">Reported at ${new Date(alert.ts).toLocaleTimeString()}</p>
                </div>
            </div>`).join('')}</div>`;
};

const renderNodesList = () => {
    const listContainer = document.getElementById('nodes-list');
    const searchTerm = document.getElementById('node-search').value.toLowerCase();
    listContainer.innerHTML = Object.values(systemState.nodes)
        .filter(node => node.name.toLowerCase().includes(searchTerm))
        .sort((a,b) => b.density - a.density)
        .map(node => {
            const colorClass = getNodeColorClass(node.density);
            return `<div class="list-item p-3 rounded-lg flex items-center justify-between cursor-pointer border border-slate-200" data-node-name="${node.name}">
                <div>
                    <p class="font-semibold text-slate-800">${node.name}</p>
                    <p class="text-sm text-slate-500">🚗 ${node.vehicleClasses.cars} | 🏍️ ${node.vehicleClasses.twoWheelers} | 🛺 ${node.vehicleClasses.autos}</p>
                </div>
                <div class="flex items-center gap-3">
                    <span class="font-bold text-lg text-slate-700">${node.density}</span>
                    <div class="w-5 h-5 rounded-full ${colorClass}"></div>
                </div>
            </div>`;
        }).join('');
};

const renderViolationsList = () => {
    const listContainer = document.getElementById('violations-list');
    listContainer.innerHTML = systemState.violations.slice(0, 50).map(v => {
        let detailsHtml = `License: <span class="font-mono">${v.details.license}</span>`;
        if (v.type === 'Speeding') detailsHtml += ` | Speed: <span class="font-semibold">${v.details.speed}/${v.details.limit} km/h</span>`;
        if (v.type === 'No Helmet') detailsHtml += ` | Offender: ${v.details.offender}`;
        const statusColor = v.challanStatus === 'Paid' ? 'text-emerald-600 bg-emerald-100' : (v.challanStatus === 'Pending' ? 'text-amber-600 bg-amber-100' : 'text-slate-500 bg-slate-100');
        return `<div class="list-item p-3 rounded-lg border border-slate-200">
            <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start">
                <div>
                    <p class="font-semibold text-slate-800">${v.type} Violation</p>
                    <p class="text-sm text-slate-600">${v.node}</p>
                    <p class="text-xs text-slate-500 mt-1">${detailsHtml}</p>
                </div>
                <div class="mt-2 sm:mt-0 flex flex-col items-start sm:items-end gap-2">
                    <span class="text-xs font-bold px-2 py-1 rounded-full ${statusColor}">${v.challanStatus}</span>
                    <button data-id="${v.id}" class="generate-challan-btn text-xs px-3 py-1 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed" ${v.challanStatus !== 'Not Generated' ? 'disabled' : ''}>
                        Generate Challan
                    </button>
                </div>
            </div>
        </div>`;
    }).join('');
};

const setupEventListeners = () => {
    document.getElementById('pause-resume-btn').addEventListener('click', () => {
        systemState.isRunning = !systemState.isRunning;
        const btn = document.getElementById('pause-resume-btn');
        const indicator = document.getElementById('status-indicator');
        const statusText = indicator.childNodes[2];

        if (systemState.isRunning) {
            btn.textContent = 'Pause System';
            btn.classList.replace('bg-emerald-600', 'bg-slate-700');
            indicator.classList.replace('text-red-600', 'text-emerald-600');
            indicator.querySelector('.bg-red-500')?.classList.replace('bg-red-500', 'bg-emerald-500');
            indicator.querySelector('.bg-red-400')?.classList.replace('bg-red-400', 'bg-emerald-400');
            indicator.innerHTML = `<span class="relative flex h-3 w-3"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span></span> System Live`;

        } else {
            btn.textContent = 'Resume System';
            btn.classList.replace('bg-slate-700', 'bg-emerald-600');
            indicator.classList.replace('text-emerald-600', 'text-red-600');
            indicator.innerHTML = `<span class="relative flex h-3 w-3"><span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span> System Paused`;
        }
    });
    document.getElementById('node-search').addEventListener('input', renderNodesList);
    document.getElementById('nodes-list').addEventListener('click', (e) => {
        const target = e.target.closest('.list-item');
        if (target) openModal(target.dataset.nodeName);
    });

    document.getElementById('modal-close-btn').addEventListener('click', closeModal);
    document.getElementById('modal-close-btn-2').addEventListener('click', closeModal);
    document.getElementById('node-modal').addEventListener('click', (e) => {
        if(e.target.id === 'node-modal') closeModal();
    });
    
    document.getElementById('ai-advisor-btn').addEventListener('click', handleAiAdvisor);
    document.getElementById('ai-advisor-close-btn').addEventListener('click', closeModal);
    document.getElementById('ai-advisor-close-btn-2').addEventListener('click', closeModal);
    document.getElementById('ai-advisor-modal').addEventListener('click', (e) => {
        if(e.target.id === 'ai-advisor-modal') closeModal();
    });


    document.getElementById('traffic-profile-select').onchange = (e) => { systemState.aiFeatures.profile = e.target.value; };
    
    document.getElementById('echallan-close-btn').addEventListener('click', closeModal);
    document.getElementById('echallan-modal').addEventListener('click', e => {
        if(e.target.id === 'echallan-modal') closeModal();
        if(e.target.id === 'mark-paid-btn') {
            const violationId = parseInt(e.target.dataset.id);
            const violation = systemState.violations.find(v => v.id === violationId);
            if (violation) {
                violation.challanStatus = 'Paid';
                renderViolationsList();
                openEChallanModal(violationId);
            }
        }
    });

    document.getElementById('violations-list').addEventListener('click', e => {
        const target = e.target.closest('.generate-challan-btn');
        if(target) {
            const violationId = parseInt(target.dataset.id);
            const violation = systemState.violations.find(v => v.id === violationId);
            if(violation) {
                violation.challanStatus = 'Pending';
                openEChallanModal(violationId);
                renderViolationsList();
            }
        }
    });

    document.getElementById('incidents-list').addEventListener('click', e => {
        const target = e.target.closest('.generate-summary-btn');
        if (target) {
            const incidentId = parseInt(target.dataset.id);
            handleIncidentSummary(incidentId, target);
        }
    });

    document.getElementById('potholes-list').addEventListener('click', (e) => {
        const target = e.target.closest('.mark-repaired-btn');
        if(target) {
            const potholeId = parseInt(target.dataset.id);
            const pothole = systemState.potholes.find(p => p.id === potholeId);
            if(pothole) {
                pothole.repaired = true;
                renderPotholesList();
                updateHeaderStats();
            }
        }
    });
};

const openEChallanModal = (violationId) => {
    const violation = systemState.violations.find(v => v.id === violationId);
    if (!violation) return;
    const rtoData = mockRtoDatabase[violation.details.license] || { owner: 'N/A', address: 'N/A' };
    const bodyEl = document.getElementById('echallan-body');
    const actionsEl = document.getElementById('echallan-actions');
    bodyEl.innerHTML = `
         <div class="space-y-3 text-sm">
            <div class="grid grid-cols-2 gap-x-4 gap-y-2">
                <span class="font-medium text-slate-500">Challan ID:</span>
                <span class="font-mono text-slate-800">CH${String(violation.id).slice(-6)}</span>
                <span class="font-medium text-slate-500">Date & Time:</span>
                <span class="font-mono text-slate-800">${new Date(violation.ts * 1000).toLocaleString()}</span>
            </div>
             <div class="border-t my-3 border-slate-200"></div>
             <div class="grid grid-cols-2 gap-x-4 gap-y-2">
                <span class="font-medium text-slate-500">Vehicle Number:</span>
                <span class="font-mono font-bold text-slate-800">${violation.details.license}</span>
                <span class="font-medium text-slate-500">Owner Name:</span>
                <span class="text-slate-800">${rtoData.owner}</span>
            </div>
             <div class="border-t my-3 border-slate-200"></div>
             <div class="grid grid-cols-2 gap-x-4 gap-y-2">
                <span class="font-medium text-slate-500">Violation:</span>
                <span class="font-bold text-red-600">${violation.type}</span>
                <span class="font-medium text-slate-500">Location:</span>
                <span class="text-slate-800">${violation.node}</span>
            </div>
             <div class="border-t my-3 border-slate-200"></div>
             <div class="grid grid-cols-2 gap-x-4 gap-y-2 items-center">
                <span class="font-medium text-slate-500">Amount Due:</span>
                <span class="font-bold text-xl text-slate-900">₹1,000.00</span>
                <span class="font-medium text-slate-500">Payment Status:</span>
                <span id="challan-payment-status" class="font-bold text-lg ${violation.challanStatus === 'Paid' ? 'text-emerald-600' : 'text-amber-600'}">${violation.challanStatus}</span>
            </div>
        </div>`;
    if (violation.challanStatus === 'Paid') {
        actionsEl.innerHTML = `<p class="text-sm font-semibold text-emerald-600">Payment Confirmed</p>`;
    } else {
        actionsEl.innerHTML = `<button data-id="${violation.id}" id="mark-paid-btn" class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition text-sm font-semibold">Mark as Paid</button>`;
    }
    document.getElementById('echallan-modal').classList.remove('hidden');
};

const closeModal = () => {
    document.getElementById('node-modal').classList.add('hidden');
    document.getElementById('echallan-modal').classList.add('hidden');
    document.getElementById('ai-advisor-modal').classList.add('hidden');
};

const renderCoordinationLog = () => {
    const listContainer = document.getElementById('coordination-list');
    listContainer.innerHTML = systemState.coordinationLog.map(log => {
        let logHtml = '';
        if (log.type === 'network') {
            logHtml = `<p class="font-semibold text-slate-800">Network Alert from <span class="text-indigo-600">${log.from}</span></p>
                       <p class="text-slate-500 text-xs">Broadcast to neighbors.</p>`;
        } else if (log.type === 'dispatch') {
            logHtml = `<p class="font-semibold text-slate-800">Dispatch to <span class="text-red-600">${log.to}</span></p>
                       <p class="text-slate-500 text-xs">${log.message}</p>`;
        } else if (log.type === 'override') {
             logHtml = `<p class="font-semibold text-slate-800">Manual Override by <span class="text-amber-600">Operator</span></p>
                       <p class="text-slate-500 text-xs">${log.message}</p>`;
        }
        return `<div class="list-item p-3 rounded-lg border border-slate-200 text-sm">
                    ${logHtml}
                    <p class="text-xs text-slate-400 mt-1">${new Date(log.ts).toLocaleTimeString()}</p>
                </div>`;
    }).join('');
};

const renderPotholesList = () => {
    const listContainer = document.getElementById('potholes-list');
    if (!listContainer) return;
    listContainer.innerHTML = systemState.potholes
        .filter(p => !p.repaired)
        .sort((a,b) => b.ts - a.ts)
        .map(pothole => {
            return `<div class="list-item p-3 rounded-lg border border-slate-200">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="font-semibold text-slate-800">Pothole #${pothole.id} <span class="text-xs font-medium px-2 py-0.5 rounded-full ${pothole.severity === 'major' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}">${pothole.severity}</span></p>
                        <p class="text-sm text-slate-500">Near: ${pothole.node}</p>
                        <p class="text-xs text-slate-400 mt-1">Reported: ${new Date(pothole.ts * 1000).toLocaleString()}</p>
                    </div>
                    <button data-id="${pothole.id}" class="mark-repaired-btn text-xs px-3 py-1 bg-emerald-100 text-emerald-800 rounded-md hover:bg-emerald-200 font-semibold">Mark Repaired</button>
                </div>
            </div>`;
        }).join('');
};
const renderIncidentsList = () => {
    const list = document.getElementById('incidents-list');
    list.innerHTML = systemState.incidents.map(incident => {
        let icon = '💥';
        if (incident.type === 'wrong_way') icon = '↔️';
        if (incident.type === 'stopped_vehicle') icon = '❗';

        let statusHtml = '';
        if(incident.rerouting === 'active') {
            statusHtml = `<div class="mt-2 text-xs font-medium text-blue-800 bg-blue-100 p-2 rounded-md">AI Rerouting Active</div>`;
        } else if(incident.rerouting === 'pending') {
             statusHtml = `<div class="mt-2 text-xs font-medium text-amber-800 bg-amber-100 p-2 rounded-md">AI analyzing optimal detour...</div>`;
        }
        
        let aiSummaryHtml = '';
        if (incident.aiSummary) {
            aiSummaryHtml = `<div class="mt-3 text-xs text-slate-600 bg-slate-100 p-2 rounded-md border-l-4 border-slate-300">${incident.aiSummary}</div>`;
        }

        return `<div class="list-item p-3 rounded-lg border border-slate-200">
            <p class="font-semibold text-slate-800">${icon} ${incident.desc}</p>
            <p class="text-sm text-slate-500">Location: ${incident.node}</p>
            <p class="text-xs text-slate-400 mt-1">Time: ${new Date(incident.ts * 1000).toLocaleString()}</p>
            ${statusHtml}
            <div class="ai-summary-container mt-2" data-incident-id="${incident.id}">
                ${aiSummaryHtml}
            </div>
            <button data-id="${incident.id}" class="generate-summary-btn mt-2 text-xs px-3 py-1 bg-slate-200 text-slate-800 rounded-md hover:bg-slate-300 font-semibold" ${incident.aiSummary ? 'disabled' : ''}>
                ✨ Generate AI Summary
            </button>
        </div>`;
    }).join('');
};

const initCharts = () => {
    Chart.defaults.font.family = 'Figtree';
    Chart.defaults.color = '#64748b'; // Slate 500
    
    const vehicleCtx = document.getElementById('vehicleClassChart').getContext('2d');
    charts.vehicles = new Chart(vehicleCtx, {
        type: 'doughnut',
        data: { 
            labels: ['Cars', '2-Wheelers', 'Autos', 'Heavy'], 
            datasets: [{ data: [], backgroundColor: ['#3b82f6', '#8b5cf6', '#f59e0b', '#475569'], borderWidth: 0, hoverOffset: 8 }] 
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 15 } } } }
    });

    const predictionCtx = document.getElementById('predictionChart').getContext('2d');
    charts.predictions = new Chart(predictionCtx, {
        type: 'line',
        data: {
            datasets: [
                { label: 'Actual Density', data: [], borderColor: '#4338ca', backgroundColor: '#c7d2fe80', tension: 0.4, fill: true, pointRadius: 0 },
                { label: 'Predicted', data: [], borderColor: '#f59e0b', borderDash: [5, 5], tension: 0.4, fill: false, pointRadius: 0 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { type: 'timeseries', time: { unit: 'second' }, grid: { display: false }, ticks: { display: false } }, y: { beginAtZero: true, max: 100, grid: { color: '#e2e8f0' }, ticks: { font: { size: 10 } } } }, plugins: { legend: { display: false } } }
    });

    const incidentsCtx = document.getElementById('incidentsChart').getContext('2d');
    charts.incidents = new Chart(incidentsCtx, {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Total Incidents', data: [], backgroundColor: '#ef4444', borderRadius: 4 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, grid: { display: false }, ticks: { font: { size: 10 } } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
    });
};

const openModal = (nodeName) => {
    const node = systemState.nodes[nodeName];
    if (!node) return;
    
    const isOverridden = !!node.manualOverride;
    document.getElementById('modal-title').textContent = node.name;
    document.getElementById('modal-body').innerHTML = `
        <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="bg-slate-100 p-3 rounded-lg">
                <p class="font-medium text-slate-600">Density Score</p>
                <p class="text-2xl font-bold text-slate-900">${node.density}</p>
            </div>
            <div class="bg-indigo-100 p-3 rounded-lg">
                <p class="font-medium text-indigo-700">${isOverridden ? 'Manual Signal' : 'AI Signal'}</p>
                <p class="text-2xl font-bold text-indigo-900">${node.signal}s</p>
            </div>
        </div>
         <div class="text-sm space-y-2 p-3 bg-slate-100 rounded-lg">
            <h4 class="font-semibold text-slate-700 mb-2">Infrastructure Status</h4>
            <p><span class="font-medium">Power:</span> ${node.infrastructure.power} (Backup: ${node.infrastructure.powerBackup})</p>
            <p><span class="font-medium">Connectivity:</span> ${node.infrastructure.connectivity} (Failover: ${node.infrastructure.connectivityFailover})</p>
         </div>
         <div class="text-sm p-3 border rounded-lg ${isOverridden ? 'border-amber-400 bg-amber-50' : 'border-slate-200'}">
             <h4 class="font-semibold text-slate-700 mb-2">Human Oversight</h4>
             ${isOverridden ? `<p class="text-amber-700 font-semibold mb-2">AI is currently overridden. Expires at ${new Date(node.manualOverride.expiry).toLocaleTimeString()}</p>` : '<p class="text-xs text-slate-500 mb-2">AI is in control. Manually override signal timing in emergencies.</p>'}
             <button id="override-ai-btn" class="text-xs px-3 py-1 ${isOverridden ? 'bg-slate-400' : 'bg-amber-500'} text-white rounded-md hover:bg-amber-600">${isOverridden ? 'Release Control to AI' : 'Override AI'}</button>
         </div>
    `;
    document.getElementById('node-modal').classList.remove('hidden');
    document.getElementById('override-ai-btn').onclick = () => handleOverride(nodeName);
};

const handleOverride = (nodeName) => {
    const node = systemState.nodes[nodeName];
    if (node.manualOverride) {
        node.manualOverride = null;
        systemState.coordinationLog.unshift({ id: Date.now(), ts: Date.now(), type: 'override', message: `Manual control released for ${nodeName}.`});
    } else {
        const duration = prompt("Enter signal duration in seconds (e.g., 60):", "60");
        if (duration && !isNaN(duration)) {
            node.manualOverride = { duration: parseInt(duration), expiry: Date.now() + 300000 }; // 5 min override
            systemState.coordinationLog.unshift({ id: Date.now(), ts: Date.now(), type: 'override', message: `Signal at ${nodeName} set to ${duration}s.`});
        }
    }
    openModal(nodeName); // Refresh modal content
};

const handleIncidentSummary = async (incidentId, button) => {
    const incident = systemState.incidents.find(i => i.id === incidentId);
    if (!incident || incident.aiSummary) return;

    button.disabled = true;
    button.innerHTML = `<div class="gemini-loader w-4 h-4 border-2 border-slate-400 border-t-slate-800 rounded-full inline-block"></div> Generating...`;

    const prompt = `Generate a concise, official incident summary for a traffic control room log. Incident details: Type: ${incident.type}, Location: ${incident.node}, Time: ${new Date(incident.ts * 1000).toLocaleString('en-IN')}, Description: "${incident.desc}".`;

    const summary = await callGeminiAPI(prompt);
    incident.aiSummary = summary.replace(/\*/g, ''); // Basic formatting cleanup
    
    const container = document.querySelector(`.ai-summary-container[data-incident-id="${incidentId}"]`);
    if (container) {
        container.innerHTML = `<div class="mt-3 text-xs text-slate-600 bg-slate-100 p-2 rounded-md border-l-4 border-slate-300">${incident.aiSummary}</div>`;
    }
    button.textContent = '✨ Summary Generated';
};

const handleAiAdvisor = async () => {
    const modal = document.getElementById('ai-advisor-modal');
    const body = document.getElementById('ai-advisor-body');
    modal.classList.remove('hidden');
    body.innerHTML = `<div class="flex items-center justify-center h-full"><div class="gemini-loader w-8 h-8 border-4 border-slate-200 border-t-indigo-600 rounded-full"></div><p class="ml-4 text-slate-600">Analyzing system data... Please wait.</p></div>`;
    
    const criticalNodes = Object.values(systemState.nodes)
        .filter(n => n.density > 80)
        .map(n => `${n.name} (Density: ${n.density})`)
        .join(', ') || 'none';
        
    const activeAlerts = systemState.systemAlerts
        .filter(a => !a.resolved)
        .map(a => `${a.type} at ${a.node}`)
        .join(', ') || 'none';

    const recentIncidents = systemState.incidents
        .slice(0, 3)
        .map(i => `${i.type} at ${i.node}`)
        .join(', ') || 'none';

    const prompt = `As a senior traffic control operator in Chennai, India, provide a prioritized list of 3-4 actionable recommendations based on this real-time system snapshot. Be concise and direct. Current Time: ${new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}.
    - High-Density Nodes (>80): ${criticalNodes}
    - Active System Alerts: ${activeAlerts}
    - Recent Incidents: ${recentIncidents}`;
    
    const advice = await callGeminiAPI(prompt, true);
    body.innerHTML = `<div class="prose prose-sm max-w-none">${advice.replace(/\n/g, '<br>')}</div>`;
};

const updateCharts = () => {
    if(systemState.totalVehicleClasses) {
        const vehicleData = systemState.totalVehicleClasses;
        charts.vehicles.data.datasets[0].data = [vehicleData.cars, vehicleData.twoWheelers, vehicleData.autos, vehicleData.heavy];
        charts.vehicles.update();
    }

    const sortedNodes = Object.values(systemState.nodes).sort((a,b) => b.incidents - a.incidents).slice(0, 5);
    charts.incidents.data.labels = sortedNodes.map(n => n.city);
    charts.incidents.data.datasets[0].data = sortedNodes.map(n => n.incidents);
    charts.incidents.update();
    
    const selectedNodeName = document.getElementById('prediction-node-select').value;
    const selectedNode = systemState.nodes[selectedNodeName];
    if (selectedNode) {
        const now = Date.now();
        if (!systemState.predictionData[selectedNodeName]) systemState.predictionData[selectedNodeName] = [];
        const nodeData = systemState.predictionData[selectedNodeName];
        nodeData.push({ x: now, y: selectedNode.density });
        const predictionData = { x: now, y: selectedNode.predictedDensity };
        if(nodeData.length > MAX_PREDICTION_POINTS) nodeData.shift();
        charts.predictions.data.datasets[0].data = nodeData;
        const predictionHistory = charts.predictions.data.datasets[1].data;
        predictionHistory.push(predictionData)
        if(predictionHistory.length > MAX_PREDICTION_POINTS) predictionHistory.shift();
        charts.predictions.update('none');
    }
};

const mapLocationToNode = (location) => {
    if (!location) return "Connaught Place - Delhi";
    const locLower = location.toLowerCase();
    for (const key of Object.keys(systemState.nodes)) {
        if (key.toLowerCase().includes(locLower) || locLower.includes(systemState.nodes[key].city.toLowerCase())) {
            return key;
        }
    }
    const keys = Object.keys(systemState.nodes);
    let hash = 0;
    for (let i = 0; i < location.length; i++) {
        hash = location.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % keys.length;
    return keys[index];
};

const fetchRecentReports = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch(`${AUTH_API_URL}/reports/recent`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const reports = await response.json();
            let stateChanged = false;

            reports.forEach(report => {
                const nodeName = mapLocationToNode(report.location);
                if (report.type === 'Pothole') {
                    const exists = systemState.potholes.some(p => p.id === report.id);
                    if (!exists) {
                        systemState.potholes.unshift({
                            id: report.id,
                            severity: 'major',
                            ts: new Date(report.timestamp).getTime() / 1000,
                            repaired: report.status === 'Resolved',
                            node: nodeName
                        });
                        stateChanged = true;
                    }
                } else {
                    const exists = systemState.systemAlerts.some(a => a.id === report.id);
                    if (!exists) {
                        systemState.systemAlerts.unshift({
                            id: report.id,
                            type: report.type,
                            node: nodeName,
                            ts: new Date(report.timestamp).getTime(),
                            resolved: report.status === 'Resolved'
                        });
                        stateChanged = true;
                    }
                }
            });

            if (stateChanged) {
                updateHeaderStats();
                renderSystemAlerts();
                renderPotholesList();
                renderMapNodes();
            }
        } else {
            console.error('Failed to fetch recent reports:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching recent reports:', error);
    }
};

const initialize = () => {
    document.getElementById('last-model-update').textContent = systemState.lastModelUpdate.toLocaleDateString();
    document.getElementById('last-security-audit').textContent = systemState.lastSecurityAudit.toLocaleDateString();

    const nodeSelect = document.getElementById('prediction-node-select');
    Object.keys(systemState.nodes).forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = systemState.nodes[name].city;
        nodeSelect.appendChild(option);
        systemState.predictionData[name] = [];
    });

    setupTabs();
    setupEventListeners();
    initCharts();
    updateDashboard();
    
    // Fetch once on initialization, then poll every 5 seconds
    fetchRecentReports();
    setInterval(fetchRecentReports, 5000);

    setInterval(updateDashboard, 2500);

    const canvas = document.getElementById('map-overlay-canvas');
    const mapContainer = document.querySelector('.map-container');
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    function resizeCanvas() {
        canvas.width = mapContainer.clientWidth;
        canvas.height = mapContainer.clientHeight;
    }
    function drawNetworkAnimation() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const now = Date.now();
        systemState.coordinationLog.filter(log => log.type === 'network' && (now - log.ts < 2000)).forEach(log => {
            const fromNode = systemState.nodes[log.from];
            if (!fromNode) return;
            const fromX = parseFloat(fromNode.pos.left) / 100 * canvas.width + 12;
            const fromY = parseFloat(fromNode.pos.top) / 100 * canvas.height + 12;
            
            log.to.forEach(neighborName => {
                const toNode = systemState.nodes[neighborName];
                if (toNode) {
                    const toX = parseFloat(toNode.pos.left) / 100 * canvas.width + 12;
                    const toY = parseFloat(toNode.pos.top) / 100 * canvas.height + 12;
                    const progress = (now - log.ts) / 2000;

                    const pulseX = fromX + (toX - fromX) * progress;
                    const pulseY = fromY + (toY - fromY) * progress;

                    ctx.beginPath();
                    ctx.moveTo(fromX, fromY);
                    ctx.lineTo(toX, toY);
                    ctx.strokeStyle = `rgba(67, 56, 202, 0.2)`;
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.arc(pulseX, pulseY, 5, 0, 2 * Math.PI);
                    ctx.fillStyle = `rgba(67, 56, 202, ${1-progress})`;
                    ctx.fill();
                }
            });
        });
        animationFrameId = requestAnimationFrame(drawNetworkAnimation);
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    if(animationFrameId) cancelAnimationFrame(animationFrameId);
    drawNetworkAnimation();
};

initialize();
});
