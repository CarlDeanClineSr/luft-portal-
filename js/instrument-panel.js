// LUFT Portal - Instrument Panel JavaScript
// Analog gauge rendering and real-time data updates for cockpit display

// Global state
let latestData = null;
let lastUpdateTime = null;
let southwardStartTime = null;
let phaseStartTime = null;

// ========================================
// UTILITY FUNCTIONS
// ========================================

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

function drawAnalogGauge(canvasId, value, min, max, redZoneStart, label, unit) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height - 20;
    const radius = Math.min(width, height) - 70;
    
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
    // χ Boundary Warning
    const chiWarning = document.getElementById('chi-warning');
    if (data.chi >= 0.15) {
        chiWarning.className = 'light-indicator red';
    } else if (data.chi >= 0.14) {
        chiWarning.className = 'light-indicator amber';
    } else if (data.chi >= 0.13) {
        chiWarning.className = 'light-indicator green';
    } else {
        chiWarning.className = 'light-indicator off';
    }
    
    // Bz Southward Warning
    const bzWarning = document.getElementById('bz-warning');
    if (data.bz !== null) {
        if (data.bz <= -8) {
            bzWarning.className = 'light-indicator red';
            if (!southwardStartTime) southwardStartTime = Date.now();
        } else if (data.bz < 0) {
            bzWarning.className = 'light-indicator amber';
            if (!southwardStartTime) southwardStartTime = Date.now();
        } else {
            bzWarning.className = 'light-indicator green';
            southwardStartTime = null;
        }
    } else {
        bzWarning.className = 'light-indicator off';
        southwardStartTime = null;
    }
    
    // Storm Warning
    const stormWarning = document.getElementById('storm-warning');
    const phase = data.storm_phase.toUpperCase();
    if (phase === 'PEAK') {
        stormWarning.className = 'light-indicator red';
    } else if (phase === 'PRE' || phase === 'POST-STORM') {
        stormWarning.className = 'light-indicator amber';
    } else {
        stormWarning.className = 'light-indicator green';
    }
    
    // Violation Warning
    const violationWarning = document.getElementById('violation-warning');
    if (data.chi > 0.15) {
        violationWarning.className = 'light-indicator red';
    } else {
        violationWarning.className = 'light-indicator off';
    }
}

// ========================================
// DATA FETCHING AND UPDATE
// ========================================

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
    
    // Phase duration
    if (phaseStartTime) {
        const duration = Math.floor((now - phaseStartTime) / 1000);
        const stormDuration = document.getElementById('storm-duration');
        if (stormDuration) stormDuration.textContent = formatTime(duration);
    }
}

async function updateInstrumentPanel() {
    const data = await fetchLatestData();
    
    if (!data) {
        const updateStatus = document.getElementById('update-status');
        if (updateStatus) updateStatus.textContent = 'Connection Error';
        return;
    }
    
    latestData = data;
    lastUpdateTime = Date.now();
    
    // Update all gauges
    drawAnalogGauge('chi-gauge', data.chi, 0, 0.20, 0.15, 'CHI', '');
    
    if (data.bz !== null) {
        drawAnalogGauge('bz-gauge', data.bz, -15, 15, 10, 'Bz (nT)', '');
    }
    
    if (!isNaN(data.speed)) {
        drawAnalogGauge('speed-gauge', data.speed, 0, 800, 600, 'SPEED', 'km/s');
    }
    
    if (!isNaN(data.density)) {
        drawAnalogGauge('density-gauge', data.density, 0, 15, 8, 'DENSITY', 'p/cm³');
    }
    
    // Update digital displays
    updateDigitalDisplays(data);
    
    // Update warning lights
    updateWarningLights(data);
    
    // Update status
    const updateStatus = document.getElementById('update-status');
    if (updateStatus) updateStatus.textContent = 'Live - Updated';
}

// ========================================
// INITIALIZATION
// ========================================

window.addEventListener('DOMContentLoaded', () => {
    console.log('Instrument Panel initializing...');
    
    // Initial update
    updateInstrumentPanel();
    
    // Update data every 60 seconds
    setInterval(updateInstrumentPanel, 60000);
    
    // Update clocks every second
    setInterval(updateClocks, 1000);
    
    console.log('Instrument Panel ready!');
});
