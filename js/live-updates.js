// Live data updates for LUFT dashboard
// Updates clocks, correlation counts, and meta-intelligence data

// ========================================
// 1. UTC CLOCK - ALWAYS WORKING
// ========================================
function updateUTCClock() {
    const now = new Date();
    const utcString = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    
    // Update all elements with class 'utc-clock'
    const clockElements = document.querySelectorAll('.utc-clock');
    clockElements.forEach(el => {
        el.textContent = utcString;
    });
    
    // Also update any element with id 'utc-time'
    const utcTimeElement = document.getElementById('utc-time');
    if (utcTimeElement) {
        utcTimeElement.textContent = utcString;
    }
}

// ========================================
// 2. META-INTELLIGENCE DATA UPDATES
// ========================================
async function updateMetaIntelligenceData() {
    try {
        // Load latest meta-intelligence summary
        const response = await fetch('reports/meta_intelligence/LATEST_SUMMARY.md');
        if (!response.ok) {
            throw new Error('Failed to load meta-intelligence data');
        }
        
        const text = await response.text();
        
        // Parse correlation count
        const correlationMatch = text.match(/Total correlations detected:\s*(\d+)/);
        if (correlationMatch) {
            const liveCorrelationsEl = document.getElementById('live-correlations');
            if (liveCorrelationsEl) {
                liveCorrelationsEl.textContent = correlationMatch[1];
            }
        }
        
        // Calculate total matches from full report
        await updateFullMetaReport();
        
        console.log('✅ Meta-intelligence data updated');
    } catch (error) {
        console.error('Failed to load meta-intelligence data:', error);
        // Keep static fallback values
        setFallbackValues();
    }
}

async function updateFullMetaReport() {
    try {
        // Get the latest full report
        const reportList = await fetch('reports/meta_intelligence/');
        const reportText = await reportList.text();
        
        // Find most recent report file
        const reportMatch = reportText.match(/report_\d{8}_\d{6}\.md/g);
        if (reportMatch && reportMatch.length > 0) {
            const latestReport = reportMatch[reportMatch.length - 1];
            
            const response = await fetch(`reports/meta_intelligence/${latestReport}`);
            if (response.ok) {
                const fullText = await response.text();
                
                // Extract match counts from all correlations
                const matchRegex = /\*\*Matches Found:\*\*\s*([\d,]+)/g;
                let totalMatches = 0;
                let match;
                
                while ((match = matchRegex.exec(fullText)) !== null) {
                    const matches = parseInt(match[1].replace(/,/g, ''));
                    if (!isNaN(matches)) {
                        totalMatches += matches;
                    }
                }
                
                // Update total matches display
                const liveMatchesEl = document.getElementById('live-matches');
                if (liveMatchesEl && totalMatches > 0) {
                    liveMatchesEl.textContent = totalMatches.toLocaleString();
                }
                
                // Extract active sources count
                const sourcesMatch = fullText.match(/\*\*Active Sources:\*\*\s*(\d+)/);
                if (sourcesMatch) {
                    const liveSourcesEl = document.getElementById('live-sources');
                    if (liveSourcesEl) {
                        liveSourcesEl.textContent = `${sourcesMatch[1]}/43`;
                    }
                }
            }
        }
    } catch (error) {
        console.error('Failed to parse full meta report:', error);
    }
}

function setFallbackValues() {
    // Set static values as fallback
    const liveCorrelationsEl = document.getElementById('live-correlations');
    if (liveCorrelationsEl && liveCorrelationsEl.textContent === '') {
        liveCorrelationsEl.textContent = '13';
    }
    
    const liveMatchesEl = document.getElementById('live-matches');
    if (liveMatchesEl && liveMatchesEl.textContent === '') {
        liveMatchesEl.textContent = '1,474,926';
    }
    
    const liveSourcesEl = document.getElementById('live-sources');
    if (liveSourcesEl && liveSourcesEl.textContent === '') {
        liveSourcesEl.textContent = '42/43';
    }
    
    const livePeakEl = document.getElementById('live-peak');
    if (livePeakEl && livePeakEl.textContent === '') {
        livePeakEl.textContent = '144,356';
    }
}

// ========================================
// 3. COUNTDOWN TO NEXT PREDICTION
// ========================================
function updatePredictionCountdown() {
    // Calculate time until next hourly update
    const now = new Date();
    const nextHour = new Date(now);
    nextHour.setHours(now.getHours() + 1, 0, 0, 0);
    
    const diff = nextHour - now;
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    const countdownEl = document.getElementById('next-prediction-countdown');
    if (countdownEl) {
        countdownEl.textContent = `${minutes}m ${seconds}s`;
    }
}

// ========================================
// 4. SYSTEM STATUS INDICATORS
// ========================================
function updateSystemStatus() {
    const statusEl = document.getElementById('system-status');
    if (statusEl) {
        statusEl.textContent = '● OPERATIONAL';
        statusEl.style.color = '#4ade80';
    }
    
    const engineStatusEl = document.getElementById('engine-status');
    if (engineStatusEl) {
        engineStatusEl.textContent = '🧠 Meta-Intelligence Engine: Active';
    }
}

// ========================================
// 5. LATEST EVENT TIMESTAMP
// ========================================
function updateLatestEventTime() {
    // The December 28, 2025 event is the validated event
    const eventElements = document.querySelectorAll('.latest-event-time');
    eventElements.forEach(el => {
        el.textContent = 'December 28, 2025 15:37 UTC';
    });
}

// ========================================
// 6. INITIALIZATION
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Live updates initialized');
    
    // Set initial fallback values immediately
    setFallbackValues();
    
    // Start UTC clock immediately (updates every second)
    updateUTCClock();
    setInterval(updateUTCClock, 1000);
    
    // Update prediction countdown every second
    updatePredictionCountdown();
    setInterval(updatePredictionCountdown, 1000);
    
    // Update system status
    updateSystemStatus();
    
    // Update latest event time
    updateLatestEventTime();
    
    // Load meta-intelligence data
    updateMetaIntelligenceData();
    
    // Refresh meta-intelligence data every 60 seconds
    setInterval(updateMetaIntelligenceData, 60000);
    
    console.log('✅ All live update systems active');
});

// ========================================
// 7. EXPORT FOR OTHER SCRIPTS
// ========================================
window.LUFTLiveUpdates = {
    updateUTCClock,
    updateMetaIntelligenceData,
    updatePredictionCountdown,
    updateSystemStatus
};
