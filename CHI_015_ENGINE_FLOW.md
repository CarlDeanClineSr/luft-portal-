# **χ = 0.15 Engine Behavior Flow**

This document describes how χ = 0.15 boundary physics flows through the  engine. 

---

## **1. DATA INGESTION**

### **Solar Wind Data Arrives (Hourly)**

**Source:** DSCOVR L1, ACE

**Input:**
```
timestamp, bt_nT, bx_gsm, by_gsm, bz_gsm, speed_km_s, density_n_cc, temperature_K
```

---

## **2. χ COMPUTATION**

### **Baseline Calculation**

```python
# Moving window baseline (e.g., 3-hour window)
df['baseline'] = df['bt_nT'].rolling(window=36, center=True).median()
```

### **χ Amplitude**

```python
# Normalized perturbation
df['chi_amplitude'] = np.abs(df['bt_nT'] - df['baseline']) / df['baseline']
```

**Safe division (handles baseline ≈ 0):**
```python
numerator = np.abs(df['bt_nT'] - df['baseline'])
chi_array = np.divide(
    numerator. to_numpy(),
    df['baseline'].to_numpy(),
    out=np.full_like(df['baseline'], np.nan, dtype=float),
    where=df['baseline'] != 0
)
df['chi_amplitude'] = chi_array
```

---

## **3. χ CLASSIFICATION**

### **Apply Universal Boundary Constants**

```python
CHI_BOUNDARY_MIN = 0.145
CHI_BOUNDARY_MAX = 0.155
```

### **Classify Each Observation**

```python
def classify_chi_status(chi_val):
    if pd.isna(chi_val):
        return 'UNKNOWN'
    elif chi_val > CHI_BOUNDARY_MAX: 
        return 'VIOLATION'
    elif CHI_BOUNDARY_MIN <= chi_val <= CHI_BOUNDARY_MAX:
        return 'AT_BOUNDARY'
    else: 
        return 'BELOW'

df['chi_status'] = df['chi_amplitude'].apply(classify_chi_status)
df['chi_at_boundary'] = (df['chi_status'] == 'AT_BOUNDARY').astype(int)
df['chi_violation'] = (df['chi_status'] == 'VIOLATION').astype(int)
```

---

## **4. BOUNDARY STATISTICS**

### **Compute Aggregates**

```python
total_obs = len(df)
at_boundary_count = df['chi_at_boundary'].sum()
violation_count = df['chi_violation'].sum()

at_boundary_pct = (at_boundary_count / total_obs) * 100
violation_pct = (violation_count / total_obs) * 100
```

### **Detect Attractor State**

```python
attractor_state = at_boundary_pct > 50. 0
```

---

## **5. ALERT GENERATION**

### **Check Alert Conditions**

```python
if violation_count > 0:
    alert_type = "WARNING"
    alert_msg = f"⚠️ {violation_count} χ VIOLATIONS DETECTED (χ > 0.155)"
    
elif attractor_state: 
    alert_type = "INFO"
    alert_msg = f"✅ ATTRACTOR STATE CONFIRMED ({at_boundary_pct:.1f}% at boundary)"
    
else:
    alert_type = "NOMINAL"
    alert_msg = f"System normal ({at_boundary_pct:.1f}% at boundary)"
```

---

## **6. DATA PRODUCTS**

### **Enhanced CSV (CME Heartbeat)**

```python
# Save with χ classification columns
df.to_csv('data/cme_heartbeat_log_2025_12.csv', index=False)
```

**Output columns:**
```
timestamp_utc, chi_amplitude, chi_at_boundary, chi_violation, chi_status, ... 
```

### **Boundary Tracking Log (JSONL)**

```python
import json

summary = {
    'timestamp':  datetime.utcnow().isoformat(),
    'total_observations': int(total_obs),
    'at_boundary_count': int(at_boundary_count),
    'at_boundary_pct':  float(at_boundary_pct),
    'violations_count': int(violation_count),
    'violations_pct': float(violation_pct),
    'status': 'ATTRACTOR' if attractor_state else 'VIOLATION' if violation_count > 0 else 'NOMINAL'
}

with open('data/chi_boundary_tracking. jsonl', 'a') as f:
    f.write(json.dumps(summary) + '\n')
```

---

## **7. DASHBOARD UPDATE**

### **Generate χ Boundary Section**

```python
boundary_html = f"""
<div class="chi-boundary-status">
    <h2>χ = 0.15 Universal Boundary Status</h2>
    
    <div class="metrics">
        <div class="metric">
            <span class="label">At Boundary: </span>
            <span class="value">{at_boundary_count} ({at_boundary_pct:.1f}%)</span>
        </div>
        
        <div class="metric">
            <span class="label">Violations:</span>
            <span class="value {'alert' if violation_count > 0 else ''}">{violation_count} ({violation_pct:.2f}%)</span>
        </div>
    </div>
    
    <div class="status">
        <strong>Status:</strong> {alert_msg}
    </div>
</div>
"""
```

---

## **8. VAULT NARRATOR REPORT**

### **Analyze χ Boundary Status**

```python
def analyze_chi_boundary(df):
    chi_values = df['chi_amplitude'].dropna()
    
    if len(chi_values) == 0:
        return None
        
    at_boundary_count = ((chi_values >= 0.145) & (chi_values <= 0.155)).sum()
    violation_count = (chi_values > 0.155).sum()
    at_boundary_pct = (at_boundary_count / len(chi_values)) * 100
    
    report = f"\n**χ = 0.15 Universal Boundary:**\n"
    report += f"- At boundary: {at_boundary_count} ({at_boundary_pct:.1f}%)\n"
    
    if violation_count > 0:
        report += f"- ⚠️ **{violation_count} VIOLATIONS DETECTED**\n"
        report += f"- Status:  Investigating filamentary breakdown\n"
    elif at_boundary_pct > 50:
        report += f"- ✅ **ATTRACTOR STATE CONFIRMED**\n"
        report += f"- System at optimal coupling\n"
    else:
        report += f"- Status: Normal operations\n"
        
    return report
```

---

## **9. COMMIT & PUSH**

### **Git Operations**

```bash
git add data/cme_heartbeat_log_2025_12.csv
git add data/chi_boundary_tracking. jsonl
git add docs/chi_dashboard.html
git commit -m "data: χ boundary analysis $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
git pull --rebase origin main --autostash
git push
```

---

## **10. WORKFLOW COMPLETION**

### **Success Output**

```
✅ χ = 0.15 BOUNDARY ANALYSIS COMPLETE

Total observations: 1,200
At boundary (0.145-0.155): 643 (53.6%)
Below boundary (<0.145): 557 (46.4%)
Violations (>0.155): 0 (0.00%)

Status: ✅ ATTRACTOR STATE CONFIRMED
System spending >50% time at optimal coupling. 

Dashboard updated:  docs/chi_dashboard.html
Tracking log updated: data/chi_boundary_tracking.jsonl
Narrator report generated. 
```

---

## **FLOW DIAGRAM**

```
Data Ingestion
      ↓
χ Computation (bt, baseline → chi_amplitude)
      ↓
χ Classification (BELOW / AT_BOUNDARY / VIOLATION)
      ↓
Boundary Statistics (%, counts, attractor state)
      ↓
Alert Generation (INFO / WARNING / CRITICAL)
      ↓
Data Products (CSV, JSONL, Dashboard HTML)
      ↓
Vault Narrator Report
      ↓
Commit & Push
      ↓
Workflow Complete
```

---

**END FLOW DOCUMENT**
