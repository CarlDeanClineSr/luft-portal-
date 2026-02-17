// Prediction engine for χ boundary response
// Uses 13 temporal correlation modes to predict future χ behavior

async function generatePrediction() {
    try {
        // Load correlation data
        const response = await fetch('data/link_intelligence/correlation_stats.json');
        if (!response.ok) throw new Error('Correlation data not available');
        
        const corrData = await response.json();
        
        // Get current time
        const now = new Date();
        const nowStr = now.toUTCString();
        
        // Generate prediction timeline
        const predictionOutput = document.getElementById('prediction-output');
        if (!predictionOutput) return;
        
        predictionOutput.innerHTML = `
            <div class="prediction-header">
                <h3>🔮 72-Hour χ Boundary Prediction</h3>
                <p class="prediction-timestamp">Based on hypothetical NOAA event at: ${nowStr}</p>
                <p class="prediction-note">Using ${corrData.total_correlations} validated correlation modes (${corrData.confidence_level}% confidence)</p>
            </div>
            
            <div class="prediction-timeline">
                ${corrData.correlation_modes.map(mode => {
                    const futureTime = new Date(now.getTime() + mode.delay_hours * 3600000);
                    const isPeak = mode.label === 'PEAK';
                    const isHighActivity = mode.matches > 120000;
                    
                    return `
                        <div class="prediction-step ${isPeak ? 'peak' : ''} ${isHighActivity ? 'high-activity' : ''}">
                            <div class="step-time">
                                <div class="step-hours">+${mode.delay_hours}h</div>
                                <div class="step-datetime">${futureTime.toLocaleString('en-US', { 
                                    month: 'short', 
                                    day: 'numeric', 
                                    hour: '2-digit', 
                                    minute: '2-digit',
                                    timeZone: 'UTC'
                                })} UTC</div>
                            </div>
                            <div class="step-info">
                                <div class="step-label">${mode.label} ${isPeak ? '🔥' : ''}</div>
                                <div class="step-description">${mode.description}</div>
                                <div class="step-confidence">
                                    ${mode.matches.toLocaleString()} historical matches
                                    ${isPeak ? '<br><strong>HIGHEST CORRELATION</strong>' : ''}
                                </div>
                            </div>
                            <div class="step-indicator">
                                <div class="indicator-bar" style="width: ${Math.min(100, (mode.matches / corrData.peak_correlation.matches) * 100)}%"></div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
            
            <div class="prediction-summary">
                <h4>⚡ Key Prediction Points:</h4>
                <ul>
                    <li><strong>0-6 hours:</strong> Immediate electromagnetic response (light speed)</li>
                    <li><strong>12-24 hours:</strong> Solar wind/CME plasma arrival - <span class="highlight-peak">PEAK CORRELATION at 24h</span></li>
                    <li><strong>36-48 hours:</strong> Main geomagnetic storm phase</li>
                    <li><strong>54-72 hours:</strong> Recovery phase and return to baseline</li>
                </ul>
                
                <div class="prediction-validation">
                    <strong>✅ Real-World Validation:</strong> December 28, 2025 event matched 6-hour correlation perfectly
                    (NOAA: 09:38 UTC → χ: 15:37 UTC)
                </div>
            </div>
        `;
        
        // Scroll to output
        predictionOutput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Error generating prediction:', error);
        const predictionOutput = document.getElementById('prediction-output');
        if (predictionOutput) {
            predictionOutput.innerHTML = `
                <div class="prediction-error">
                    <p>⚠️ Unable to generate prediction: ${error.message}</p>
                    <p>Please ensure correlation data is available.</p>
                </div>
            `;
        }
    }
}

// Generate prediction for a specific NOAA event time
async function generatePredictionForEvent(noaaEventTime) {
    try {
        const response = await fetch('data/link_intelligence/correlation_stats.json');
        if (!response.ok) throw new Error('Correlation data not available');
        
        const corrData = await response.json();
        const eventTime = new Date(noaaEventTime);
        
        const predictions = corrData.correlation_modes.map(mode => {
            const responseTime = new Date(eventTime.getTime() + mode.delay_hours * 3600000);
            return {
                delay_hours: mode.delay_hours,
                response_time: responseTime,
                label: mode.label,
                description: mode.description,
                matches: mode.matches,
                confidence: Math.round((mode.matches / corrData.total_matches) * 100)
            };
        });
        
        return {
            event_time: eventTime,
            predictions: predictions,
            total_correlations: corrData.total_correlations,
            confidence_level: corrData.confidence_level,
            peak: corrData.peak_correlation
        };
    } catch (error) {
        console.error('Error generating event prediction:', error);
        return null;
    }
}

// Get next expected χ response time based on latest NOAA activity
async function getNextExpectedResponse() {
    // This would integrate with real NOAA data feeds
    // For now, returns a placeholder based on correlation data
    try {
        const response = await fetch('data/link_intelligence/correlation_stats.json');
        if (!response.ok) throw new Error('Correlation data not available');
        
        const corrData = await response.json();
        
        // Use validation event as reference
        if (corrData.validation_event) {
            const noaaTime = new Date(corrData.validation_event.date + 'T' + corrData.validation_event.noaa_event_time);
            const chiTime = new Date(corrData.validation_event.date + 'T' + corrData.validation_event.chi_response_time);
            
            return {
                noaa_event: noaaTime.toUTCString(),
                chi_response: chiTime.toUTCString(),
                delay_hours: corrData.validation_event.delay_hours,
                status: corrData.validation_event.status
            };
        }
        
        return null;
    } catch (error) {
        console.error('Error getting next response:', error);
        return null;
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generatePrediction,
        generatePredictionForEvent,
        getNextExpectedResponse
    };
}
