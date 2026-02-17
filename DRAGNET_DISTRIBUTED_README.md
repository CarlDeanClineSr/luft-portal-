# Dragnet Distributed Survey System

A massively parallel stellar survey system that leverages GitHub Actions to scan up to 1 million stellar targets using distributed execution across up to 256 parallel virtual machines.

## Overview

This system implements a distributed computing framework that:
- Generates deterministic sky positions using Fibonacci sphere algorithm
- Distributes work across parallel GitHub Actions runners
- Aggregates results from all workers into a single output
- Provides real-time progress monitoring
- Stores results as downloadable artifacts

## Files

### 1. Workflow File
**Location**: `.github/workflows/dragnet_distributed.yml`

The GitHub Actions workflow that orchestrates the distributed survey:
- **generate-matrix**: Creates job matrix dynamically based on inputs
- **dragnet-scan**: Runs up to 256 parallel worker jobs
- **aggregate-results**: Collects and combines all worker outputs

### 2. Worker Script
**Location**: `dragnet_distributed_worker.py`

Python script executed by each worker job:
- Accepts job parameters via command-line arguments
- Generates deterministic target coordinates
- Placeholder for ASAS-SN query logic (to be implemented)
- Reports progress every 100 targets
- Outputs results in JSON format

### 3. Aggregator Script
**Location**: `scripts/aggregate_dragnet_results.py`

Combines results from all worker jobs:
- Collects JSON files from all workers
- Aggregates into single comprehensive output
- Handles missing or malformed files gracefully

## Usage

### Running the Survey

1. **Navigate to GitHub Actions**
   - Go to your repository on GitHub
   - Click the "Actions" tab

2. **Select the Workflow**
   - In the left sidebar, click "Dragnet Distributed Survey"

3. **Run the Workflow**
   - Click "Run workflow" dropdown button
   - Set parameters:
     - **Total targets**: Number of stars to scan (e.g., 100000)
     - **Batch size**: Stars per worker job (e.g., 1000)
   - Click green "Run workflow" button

### Monitoring Progress

1. **View the Workflow Run**
   - Click on the newly created workflow run
   - You'll see three job sections:
     - `generate-matrix`: Completes in ~5 seconds
     - `dragnet-scan`: Shows vacuum of parallel jobs
     - `aggregate-results`: Runs after all scans complete

2. **Check Individual Jobs**
   - Click any job in the `dragnet-scan` vacuum
   - View live logs showing progress:
     ```
     Scanning 1000 targets...
     Progress: 100/1000 (10.0%)
     Progress: 200/1000 (20.0%)
     ...
     ✅ Job 42 complete
     ```

### Downloading Results

After the workflow completes:

1. Scroll to bottom of workflow run page
2. Under "Artifacts" section, you'll see:
   - `dragnet-job-0`, `dragnet-job-1`, ... (individual job results)
   - `dragnet-survey-complete` (aggregated results)
3. Click `dragnet-survey-complete` to download
4. Extract the ZIP file to access `reports/dragnet_survey_<timestamp>.json`

## Output Format

### Individual Job Output
```json
{
  "job_id": 42,
  "results": [
    {
      "ra": 240.256,
      "dec": 27.611,
      "analysis": {
        "flux_ratio": 50.7,
        "is_stress_node": true
      }
    }
  ]
}
```

### Aggregated Output
```json
{
  "total_scanned": 87234,
  "results": [
    ...all results from all jobs...
  ]
}
```

## Configuration

### Scaling Parameters

- **Default**: 100,000 targets, 1,000 per batch = 100 parallel jobs
- **Maximum**: GitHub Actions limit is 256 concurrent jobs
- **Recommended for 1M targets**: batch_size = 4000 (250 jobs)

### Workflow Timeouts

- Each worker job has a 360-minute (6-hour) timeout
- Individual job failures don't stop other jobs (`fail-fast: false`)

## Development

### Testing Locally

```bash
# Test worker script
python3 dragnet_distributed_worker.py \
  --job-id 0 \
  --total-targets 100 \
  --batch-size 10 \
  --n-jobs 10 \
  --output /tmp/test/job_0.json

# Test aggregator
python3 scripts/aggregate_dragnet_results.py \
  --input-dir /tmp/test \
  --output /tmp/test/final.json
```

### Adding Query Logic

The worker script currently has placeholder logic. To implement actual stellar queries:

1. Edit `dragnet_distributed_worker.py`
2. Find the TODO comment in the scan loop
3. Implement ASAS-SN queries using the `client` object
4. Append results to the `results` list

Example:
```python
if client:
    # Query ASAS-SN for light curve data
    data = client.query_position(ra, dec, radius=0.01)
    
    # Analyze for stress nodes
    if data and len(data) > 100:
        flux_ratio = calculate_flux_ratio(data)
        if flux_ratio > 5.0:
            results.append({
                'ra': ra,
                'dec': dec,
                'flux_ratio': flux_ratio,
                'is_stress_node': True
            })
```

## Architecture

```
GitHub Actions (256 parallel runners)
├── Job 0: Scans targets 0-999
├── Job 1: Scans targets 1000-1999
├── Job 2: Scans targets 2000-2999
│   ...
└── Job 255: Scans targets 255000-255999

↓ All jobs complete ↓

Aggregator Job
└── Combines all results → Final JSON
```

## Security

- All jobs run with minimal permissions (`contents: read`)
- No secrets or credentials required for basic operation
- CodeQL security scan: 0 vulnerabilities

## Dependencies

Installed automatically by workflow:
- Python 3.11
- numpy, pandas
- skypatrol / pyasassn (for ASAS-SN queries)
- astroquery, astropy, lightkurve

## Troubleshooting

### Workflow doesn't appear
- Check YAML syntax in `.github/workflows/dragnet_distributed.yml`
- Ensure file is committed to repository

### Jobs fail with "Module not found"
- Dependencies are installed automatically
- Check individual job log for specific module

### Empty results
- This is expected behavior with placeholder logic
- Implement actual query logic in worker script

### Jobs timeout
- Reduce `batch_size` to scan fewer targets per job
- Check if API rate limiting is an issue

## Next Steps

1. Implement ASAS-SN query logic in worker script
2. Run test survey with 100k targets
3. Validate results format and quality
4. Scale up to 1M targets for full survey

## References

- [ASAS-SN Sky Patrol](https://asas-sn.osu.edu/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Fibonacci Sphere Algorithm](https://en.wikipedia.org/wiki/Fibonacci_sphere)
