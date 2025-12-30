// LUFT Portal - Instrument Panel JavaScript
// Analog gauge rendering and real-time data updates for cockpit display

// Global state
let latestData = null;
let lastUpdateTime = null;
let southwardStartTime = null;
let phaseStartTime = null;
let prePhaseStartTime = null;
let estimatedPeakTime = null;

// Needle animation state
let needlePositions = {
    chi: 0,
    bz: 0,
    speed: 0,
    density: 0
};

let targetNeedlePositions = {
    chi: 0,
    bz: 0,
    speed: 0,
    density: 0
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

function lerp(start, end, t) {
    return start + (end - start) * Math.min(1, t);
}

function parseCSVLine(line) {
    const values = line.split(',');
    
    if (values.length >= 9) {
        const chi = parseFloat(values[1]);
        const bzRaw = values[6];
        const bz = (bzRaw && bzRaw.trim() !== '') ? parseFloat(bzRaw) : null;
        
        return {
            timestamp: values[0],
            chi: chi,
            phase: parseFloat(values[2]),
            storm_phase: values[3],
            density: parseFloat(values[4]),
            speed: parseFloat(values[5]),
            bz: bz,
            bt: parseFloat(values[7]),
            source: values[8]
        };
    }
    return null;
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// ========================================
// ANALOG GAUGE RENDERING
// ========================================

function drawAnalogGauge(canvasId, value, min, max, redZoneStart, label, unit, animated = true) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height - 20;
    const radius = Math.min(width, height) - 70;
    
    // Get gauge key from canvas ID
    const gaugeKey = canvasId.replace('-gauge', '');
    
    // Update target position
    if (animated) {
        targetNeedlePositions[gaugeKey] = value;
        // Smooth animation - lerp current position toward target
        needlePositions[gaugeKey] = lerp(needlePositions[gaugeKey], targetNeedlePositions[gaugeKey], 0.15);
        value = needlePositions[gaugeKey];
    }
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw outer bezel
    const gradient = ctx.createRadialGradient(centerX, centerY, radius - 10, centerX, centerY, radius + 10);
    gradient.addColorStop(0, '#444');
    gradient.addColorStop(0.5, '#666');
    gradient.addColorStop(1, '#333');
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius + 5, Math.PI, 2 * Math.PI);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 10;
    ctx.stroke();
    
    // Draw gauge background
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 25;
    ctx.stroke();
    
    // Draw colored sections
    const range = max - min;
    const redZoneAngle = Math.PI + ((redZoneStart - min) / range) * Math.PI;
    
    // Green section
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, redZoneAngle);
    ctx.strokeStyle = '#4ade80';
    ctx.lineWidth = 22;
    ctx.stroke();
    
    // Red section
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, redZoneAngle, 2 * Math.PI);
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 22;
    ctx.stroke();
    
    // Draw tick marks
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 2;
    const numTicks = 10;
    
    for (let i = 0; i <= numTicks; i++) {
        const angle = Math.PI + (i / numTicks) * Math.PI;
        const tickLength = i % 2 === 0 ? 15 : 8;
        const startRadius = radius - tickLength;
        
        const x1 = centerX + Math.cos(angle) * startRadius;
        const y1 = centerY + Math.sin(angle) * startRadius;
        const x2 = centerX + Math.cos(angle) * radius;
        const y2 = centerY + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }
    
    // Draw scale numbers
    ctx.fillStyle = '#e0e0e0';
    ctx.font = 'bold 11px "Courier New"';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const numLabels = 5;
    for (let i = 0; i <= numLabels; i++) {
        const labelValue = min + (range * i / numLabels);
        const angle = Math.PI + (i / numLabels) * Math.PI;
        const labelRadius = radius + 30;
        const x = centerX + Math.cos(angle) * labelRadius;
        const y = centerY + Math.sin(angle) * labelRadius;
        
        ctx.fillText(labelValue.toFixed(labelValue < 1 ? 2 : 0), x, y);
    }
    
    // Draw needle
    const clampedValue = Math.max(min, Math.min(max, value));
    const needleAngle = Math.PI + ((clampedValue - min) / range) * Math.PI;
    const needleLength = radius - 15;
    
    // Needle shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 3;
    ctx.shadowOffsetY = 3;
    
    // Needle body
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
        centerX + Math.cos(needleAngle) * needleLength,
        centerY + Math.sin(needleAngle) * needleLength
    );
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 4;
    ctx.stroke();
    
    // Reset shadow
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    
    // Center hub
    const hubGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 12);
    hubGradient.addColorStop(0, '#666');
    hubGradient.addColorStop(0.5, '#444');
    hubGradient.addColorStop(1, '#222');
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, 12, 0, 2 * Math.PI);
    ctx.fillStyle = hubGradient;
    ctx.fill();
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Center dot
    ctx.beginPath();
    ctx.arc(centerX, centerY, 3, 0, 2 * Math.PI);
    ctx.fillStyle = '#ff0000';
    ctx.fill();
    
    // Label at bottom
    ctx.fillStyle = '#4da3ff';
    ctx.font = 'bold 12px "Courier New"';
    ctx.textAlign = 'center';
    ctx.fillText(label, centerX, height - 5);
}

// ========================================
// WARNING LIGHTS
// ========================================

function updateWarningLights(data) {
    // χ Boundary Warning with redline animation
    const chiWarning = document.getElementById('chi-warning');
    const CHI_BOUNDARY_TOLERANCE = 0.001; // Tolerance for boundary detection
    
    if (data.chi >= 0.15) {
        chiWarning.className = 'light-indicator red';
        // Add extra pulsing for boundary violation (within tolerance of redline)
        const atBoundary = Math.abs(data.chi - 0.15) < CHI_BOUNDARY_TOLERANCE;
        if (atBoundary) {
            chiWarning.style.animation = 'pulse-red 0.5s infinite';
        }
    } else if (data.chi >= 0.14) {
        chiWarning.className = 'light-indicator amber';
    } else if (data.chi >= 0.13) {
        chiWarning.className = 'light-indicator green';
    } else {
        chiWarning.className = 'light-indicator off';
    }
    
    // Bz Southward Warning with flash animation
    const bzWarning = document.getElementById('bz-warning');
    if (data.bz !== null) {
        if (data.bz <= -8) {
            bzWarning.className = 'light-indicator red';
            bzWarning.style.animation = 'pulse-red 0.6s infinite';
            if (!southwardStartTime) southwardStartTime = Date.now();
        } else if (data.bz < 0) {
            bzWarning.className = 'light-indicator amber';
            bzWarning.style.animation = 'pulse-amber 1.2s infinite';
            if (!southwardStartTime) southwardStartTime = Date.now();
        } else {
            bzWarning.className = 'light-indicator green';
            bzWarning.style.animation = 'none';
            southwardStartTime = null;
        }
    } else {
        bzWarning.className = 'light-indicator off';
        bzWarning.style.animation = 'none';
        southwardStartTime = null;
    }
    
    // Storm Warning
    const stormWarning = document.getElementById('storm-warning');
    const phase = data.storm_phase.toUpperCase();
    if (phase === 'PEAK') {
        stormWarning.className = 'light-indicator red';
        stormWarning.style.animation = 'pulse-red 0.8s infinite';
    } else if (phase === 'PRE') {
        stormWarning.className = 'light-indicator amber';
        stormWarning.style.animation = 'pulse-amber 1.5s infinite';
        // Track PRE phase start for countdown
        if (!prePhaseStartTime) {
            prePhaseStartTime = Date.now();
            // Estimate peak time (typically 30-60 minutes after PRE starts)
            estimatedPeakTime = Date.now() + (45 * 60 * 1000); // 45 minutes
        }
    } else if (phase === 'POST-STORM') {
        stormWarning.className = 'light-indicator amber';
        stormWarning.style.animation = 'none';
        prePhaseStartTime = null;
        estimatedPeakTime = null;
    } else {
        stormWarning.className = 'light-indicator green';
        stormWarning.style.animation = 'none';
        prePhaseStartTime = null;
        estimatedPeakTime = null;
    }
    
    // Violation Warning
    const violationWarning = document.getElementById('violation-warning');
    if (data.chi > 0.15) {
        violationWarning.className = 'light-indicator red';
        violationWarning.style.animation = 'pulse-red 0.5s infinite';
    } else {
        violationWarning.className = 'light-indicator off';
        violationWarning.style.animation = 'none';
    }
}

// ========================================
// DATA FETCHING AND UPDATE
// ========================================

async function fetchLiveData() {
    try {
        // Try to fetch from live API first (cache busting via timestamp)
        const cacheBuster = Date.now();
        const response = await fetch(`api/get_realtime_data.py?_=${cacheBuster}`);
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'ok') {
                return {
                    timestamp: data.data_timestamp,
                    chi: data.chi,
                    phase: 0, // Phase radians not needed here
                    storm_phase: data.storm_phase,
                    density: data.density,
                    speed: data.speed,
                    bz: data.bz,
                    bt: data.bt,
                    source: data.source,
                    warnings: data.warnings
                };
            }
        }
    } catch (error) {
        console.log('Live API not available, falling back to CSV data');
    }
    
    // Fallback to CSV file
    return await fetchLatestData();
}

async function fetchLatestData() {
    try {
        const response = await fetch('data/cme_heartbeat_log_2025_12.csv?' + Date.now());
        const text = await response.text();
        const lines = text.trim().split('\n');
        
        if (lines.length < 2) return null;
        
        const lastLine = lines[lines.length - 1];
        return parseCSVLine(lastLine);
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

function updateDigitalDisplays(data) {
    // χ Value
    const chiValue = document.getElementById('chi-value');
    if (chiValue && !isNaN(data.chi)) {
        chiValue.textContent = data.chi.toFixed(4);
        chiValue.style.color = data.chi >= 0.15 ? '#ff0000' : data.chi >= 0.14 ? '#ffaa00' : '#00ff00';
    }
    
    // Bz Value
    const bzValue = document.getElementById('bz-value');
    if (bzValue && data.bz !== null) {
        bzValue.textContent = data.bz.toFixed(2);
        bzValue.style.color = data.bz < 0 ? '#ff0000' : '#00ff00';
    } else if (bzValue) {
        bzValue.textContent = 'N/A';
        bzValue.style.color = '#666';
    }
    
    // Speed Value
    const speedValue = document.getElementById('speed-value');
    if (speedValue && !isNaN(data.speed)) {
        speedValue.textContent = Math.round(data.speed);
        speedValue.style.color = data.speed >= 600 ? '#ff0000' : data.speed >= 500 ? '#ffaa00' : '#00ff00';
    }
    
    // Density Value
    const densityValue = document.getElementById('density-value');
    if (densityValue && !isNaN(data.density)) {
        densityValue.textContent = data.density.toFixed(2);
        densityValue.style.color = data.density >= 8 ? '#ff0000' : data.density >= 4 ? '#ffaa00' : '#00ff00';
    }
    
    // Storm Phase
    const stormPhase = document.getElementById('storm-phase');
    if (stormPhase) {
        const phase = data.storm_phase.toUpperCase().replace('-', ' ');
        stormPhase.textContent = phase;
        
        // Track phase changes
        if (!phaseStartTime || latestData?.storm_phase !== data.storm_phase) {
            phaseStartTime = Date.now();
        }
    }
}

function updateClocks() {
    const now = Date.now();
    
    // Update UTC clock
    const utcClock = document.getElementById('utc-clock');
    if (utcClock) {
        const time = new Date().toISOString().slice(11, 19) + ' UTC';
        utcClock.textContent = time;
    }
    
    // Time since last update
    if (lastUpdateTime) {
        const elapsed = Math.floor((now - lastUpdateTime) / 1000);
        const chiTime = document.getElementById('chi-time');
        const speedTime = document.getElementById('speed-time');
        const densityTime = document.getElementById('density-time');
        
        if (chiTime) chiTime.textContent = formatTime(elapsed);
        if (speedTime) speedTime.textContent = formatTime(elapsed);
        if (densityTime) densityTime.textContent = formatTime(elapsed);
    }
    
    // Southward duration
    if (southwardStartTime) {
        const duration = Math.floor((now - southwardStartTime) / 1000);
        const bzTime = document.getElementById('bz-time');
        if (bzTime) bzTime.textContent = formatTime(duration);
    } else {
        const bzTime = document.getElementById('bz-time');
        if (bzTime) bzTime.textContent = '00:00:00';
    }
    
    // Phase duration or countdown to peak
    const stormDuration = document.getElementById('storm-duration');
    if (stormDuration) {
        if (estimatedPeakTime && prePhaseStartTime && now < estimatedPeakTime) {
            // Countdown to peak
            const remaining = Math.floor((estimatedPeakTime - now) / 1000);
            stormDuration.textContent = '-' + formatTime(remaining);
            stormDuration.style.color = '#ff0000';
            stormDuration.style.textShadow = '0 0 15px #ff0000';
        } else if (phaseStartTime) {
            // Regular phase duration
            const duration = Math.floor((now - phaseStartTime) / 1000);
            stormDuration.textContent = formatTime(duration);
            stormDuration.style.color = '#4da3ff';
            stormDuration.style.textShadow = 'none';
        }
    }
}

async function updateInstrumentPanel() {
    const data = await fetchLiveData();
    
    if (!data) {
        const updateStatus = document.getElementById('update-status');
        if (updateStatus) updateStatus.textContent = 'Connection Error';
        return;
    }
    
    latestData = data;
    lastUpdateTime = Date.now();
    
    // Update all gauges with animation
    drawAnalogGauge('chi-gauge', data.chi, 0, 0.20, 0.15, 'CHI', '', true);
    
    if (data.bz !== null) {
        drawAnalogGauge('bz-gauge', data.bz, -15, 15, 10, 'Bz (nT)', '', true);
    }
    
    if (!isNaN(data.speed)) {
        drawAnalogGauge('speed-gauge', data.speed, 0, 800, 600, 'SPEED', 'km/s', true);
    }
    
    if (!isNaN(data.density)) {
        drawAnalogGauge('density-gauge', data.density, 0, 15, 8, 'DENSITY', 'p/cm³', true);
    }
    
    // Update digital displays
    updateDigitalDisplays(data);
    
    // Update warning lights
    updateWarningLights(data);
    
    // Start animation loop if not already running
    if (!window.animationLoopRunning) {
        window.animationLoopRunning = true;
        requestAnimationFrame(animateGauges);
    }
    
    // Update status
    const updateStatus = document.getElementById('update-status');
    if (updateStatus) {
        const source = data.source || 'CSV';
        updateStatus.textContent = `Live - ${source}`;
    }
}

// Continuous animation loop for smooth needle movement
function animateGauges() {
    if (latestData) {
        // Redraw gauges with interpolated needle positions
        drawAnalogGauge('chi-gauge', latestData.chi, 0, 0.20, 0.15, 'CHI', '', true);
        
        if (latestData.bz !== null) {
            drawAnalogGauge('bz-gauge', latestData.bz, -15, 15, 10, 'Bz (nT)', '', true);
        }
        
        if (!isNaN(latestData.speed)) {
            drawAnalogGauge('speed-gauge', latestData.speed, 0, 800, 600, 'SPEED', 'km/s', true);
        }
        
        if (!isNaN(latestData.density)) {
            drawAnalogGauge('density-gauge', latestData.density, 0, 15, 8, 'DENSITY', 'p/cm³', true);
        }
    }
    
    if (window.animationLoopRunning) {
        requestAnimationFrame(animateGauges);
    }
}

// ========================================
// INITIALIZATION
// ========================================

window.addEventListener('DOMContentLoaded', () => {
    console.log('Instrument Panel initializing...');
    
    // Initial update (which includes first animation frame)
    updateInstrumentPanel();
    
    // Update data every 60 seconds
    setInterval(updateInstrumentPanel, 60000);
    
    // Update clocks every second
    setInterval(updateClocks, 1000);
    
    console.log('Instrument Panel ready!');
});
