```json
{
  "$schema": "https://example.org/schemas/occupancy-summary-v1.json",
  "event_id": "uint64",
  "run": "uint32",
  "lumi_section": "uint32|null",
  "stream": "string",
  "source_file": "string",
  "subdetector": {
    "pixel_hits": "uint32",
    "strip_hits": "uint32",
    "ecal_rechits": "uint32",
    "hcal_rechits": "uint32",
    "muon_segments": "uint32"
  },
  "occupancy": {
    "pixel_fraction": "float",
    "strip_fraction": "float",
    "ecal_fraction": "float",
    "hcal_fraction": "float",
    "muon_fraction": "float",
    "global_fraction": "float"
  },
  "energy_flow_bins": [ "float", "... fixed length N=8" ],
  "entropy_H": "float",
  "overflow_flag": "boolean",
  "trigger_paths_sampled": [ "string" ],
  "timestamp_ns": "uint64|null"
}
```
