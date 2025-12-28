# **χ = 0.15 Quick Reference Card**

## **Constants (Use Everywhere)**

```python
CHI_CAP_THEORETICAL = 0.15
CHI_TOLERANCE = 0.01
CHI_BOUNDARY_MIN = 0.145
CHI_BOUNDARY_MAX = 0.155
```

## **Classification Function**

```python
def classify_chi_status(chi_val):
    if pd.isna(chi_val):
        return 'UNKNOWN'
    elif chi_val > 0.155:
        return 'VIOLATION'
    elif 0.145 <= chi_val <= 0.155:
        return 'AT_BOUNDARY'
    else:
        return 'BELOW'
```

## **Detection Checks**

```python
# Attractor state
attractor = (at_boundary_pct > 50.0)

# Violation alert
violation_alert = (violation_count > 0)
```

## **Data Columns to Add**

```python
df['chi_at_boundary'] = ((df['chi_amplitude'] >= 0.145) & 
                          (df['chi_amplitude'] <= 0.155)).astype(int)
df['chi_violation'] = (df['chi_amplitude'] > 0.155).astype(int)
df['chi_status'] = df['chi_amplitude'].apply(classify_chi_status)
```

## **Alert Messages**

```python
if violation_count > 0:
    print(f"⚠️ {violation_count} χ VIOLATIONS DETECTED")
elif at_boundary_pct > 50:
    print(f"✅ ATTRACTOR STATE ({at_boundary_pct:.1f}%)")
else:
    print(f"NOMINAL ({at_boundary_pct:. 1f}%)")
```

## **Files to Update**

- `scripts/luft_solar_wind_audit.py`
- `scripts/cme_heartbeat_logger.py`
- `scripts/generate_chi_dashboard.py`
- `scripts/vault_narrator_update.py`

## **Expected Results**

- **At boundary:** ~53-56% (attractor state)
- **Violations:** 0% (should NEVER exceed 0.155)
- **Status:** ATTRACTOR STATE CONFIRMED

---

**Keep this card handy when coding!**
