# Real-Time Space Weather Data API

## Overview

This API provides live space weather data from NOAA's DSCOVR satellite, including calculated χ (chi) amplitude values and storm phase determination.

## Endpoints

### GET `/api/get_realtime_data.py`

Returns current space weather conditions in JSON format.

#### Response Format

```json
{
  "status": "ok",
  "timestamp": "2025-12-30T14:41:50.470305+00:00",
  "data_timestamp": "2025-12-30 14:37:00.000",
  "chi": 0.008652063056857595,
  "storm_phase": "QUIET",
  "bz": 0.57,
  "bt": 4.66,
  "bx": -3.24,
  "by": -3.3,
  "density": 3.4,
  "speed": 411.6,
  "temperature": 88696.0,
  "source": "DSCOVR/NOAA",
  "warnings": {
    "chi_boundary": false,
    "chi_violation": false,
    "bz_southward": false,
    "bz_critical": false,
    "high_speed": false,
    "high_density": false
  }
}
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "ok" or "error" |
| `timestamp` | string | API response timestamp (ISO 8601) |
| `data_timestamp` | string | Satellite measurement timestamp |
| `chi` | float | Calculated χ amplitude (0-1+ range) |
| `storm_phase` | string | "QUIET", "PRE", "PEAK", or "POST-STORM" |
| `bz` | float | Magnetic field Z component (nT) |
| `bt` | float | Total magnetic field strength (nT) |
| `bx` | float | Magnetic field X component (nT) |
| `by` | float | Magnetic field Y component (nT) |
| `density` | float | Plasma density (protons/cm³) |
| `speed` | float | Solar wind speed (km/s) |
| `temperature` | float | Plasma temperature (K) |
| `source` | string | Data source identifier |

#### Warning Flags

| Warning | Condition | Meaning |
|---------|-----------|---------|
| `chi_boundary` | χ ≥ 0.15 | At or above universal boundary |
| `chi_violation` | χ > 0.15 | Exceeding boundary (violation) |
| `bz_southward` | Bz < 0 | Southward IMF (favorable for storms) |
| `bz_critical` | Bz < -8 | Critical southward condition |
| `high_speed` | speed ≥ 600 | High-speed solar wind stream |
| `high_density` | density ≥ 8 | Elevated plasma density |

## Chi (χ) Calculation

The χ amplitude is calculated using the LUFT formula:

```
χ = (|Bz| × √density × speed) / 50000
```

This represents the plasma coherence level, with 0.15 being the universal boundary threshold.

## Storm Phase Determination

| Phase | Condition | Description |
|-------|-----------|-------------|
| QUIET | χ < 0.13 | Normal solar wind conditions |
| PRE | χ ≥ 0.13 and Bz < -5 | Storm approaching |
| PEAK | χ > 0.15 | Active geomagnetic storm |
| POST-STORM | χ ≥ 0.13 and Bz ≥ -5 | Storm subsiding |

## Data Sources

- **NOAA SWPC Magnetic Data**: https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json
- **NOAA SWPC Plasma Data**: https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json

## Update Frequency

- **DSCOVR Satellite**: 1-minute cadence
- **Data Latency**: ~60-90 seconds
- **API Cache**: No caching, always fetches latest

## Usage Examples

### Python
```python
import requests

response = requests.get('http://your-domain/api/get_realtime_data.py')
data = response.json()

if data['status'] == 'ok':
    chi = data['chi']
    phase = data['storm_phase']
    print(f"χ = {chi:.4f}, Phase = {phase}")
    
    if data['warnings']['chi_boundary']:
        print("WARNING: At boundary!")
```

### JavaScript
```javascript
fetch('api/get_realtime_data.py')
  .then(response => response.json())
  .then(data => {
    if (data.status === 'ok') {
      console.log(`χ = ${data.chi.toFixed(4)}`);
      console.log(`Storm Phase: ${data.storm_phase}`);
      
      if (data.warnings.chi_violation) {
        alert('VIOLATION: χ exceeds 0.15!');
      }
    }
  });
```

### cURL
```bash
curl http://your-domain/api/get_realtime_data.py
```

## Error Handling

### Error Response
```json
{
  "status": "error",
  "message": "Unable to fetch DSCOVR data",
  "timestamp": "2025-12-30T14:41:50.470305+00:00"
}
```

### Common Errors
- **NOAA Service Unavailable**: Data feeds may be temporarily offline
- **Network Timeout**: Check firewall/proxy settings
- **Invalid Data**: Satellite may be in eclipse or maintenance

## Rate Limiting

No rate limiting is currently enforced, but recommended usage:
- **Web Applications**: Poll every 60 seconds
- **Monitoring Systems**: Poll every 30-60 seconds
- **Research/Analysis**: Download bulk data from NOAA archives

## Dependencies

- Python 3.7+
- `requests` library
- Internet access to NOAA SWPC servers

## Installation

```bash
pip install requests
chmod +x api/get_realtime_data.py
```

## Deployment

### CGI Mode
```bash
# Copy to web server CGI directory
cp api/get_realtime_data.py /var/www/cgi-bin/
chmod +x /var/www/cgi-bin/get_realtime_data.py
```

### Standalone
```bash
# Run as standalone script
python3 api/get_realtime_data.py
```

## Testing

```bash
# Test API locally
cd /path/to/luft-portal
python3 api/get_realtime_data.py

# Should output JSON with current data
```

## License

Open source - Free for life-saving applications (aviation, satellites, power grids)

## Support

For issues or questions:
- GitHub Issues: https://github.com/CarlDeanClineSr/luft-portal-
- Documentation: See COCKPIT_USER_GUIDE.md

## Credits

Part of the LUFT (Lattice Universal Field Theory) project
- Research: Carl Dean Cline Sr.
- Data Source: NOAA Space Weather Prediction Center
- Satellite: DSCOVR (Deep Space Climate Observatory)
