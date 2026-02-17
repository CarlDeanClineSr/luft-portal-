# Performance Best Practices for LUFT Portal

## Overview

This document outlines performance optimization patterns and anti-patterns discovered during code analysis. Following these guidelines will help maintain fast execution times, especially for scripts that run on automated schedules.

## Python Performance Guidelines

### 1. DataFrame Iteration

**❌ AVOID: `.iterrows()`**
```python
# SLOW - Creates Series objects for each row
for _, row in df.iterrows():
    result = row['column1'] + row['column2']
```

**✅ PREFER: `.apply()` with axis=1 or vectorized operations**
```python
# BEST - Apply function (2x faster than iterrows for string operations)
results = df.apply(lambda row: row['column1'] + row['column2'], axis=1).tolist()

# EXCELLENT - Vectorized operations when possible (fastest)
df['result'] = df['column1'] + df['column2']
```

**Performance Benchmarks** (1000 iterations, 20 rows):
- `iterrows()`: 1.04s (baseline)
- `iloc[]`: 1.12s (1.08x slower - not recommended)
- `apply(axis=1)`: 0.52s (2.0x faster) ✅
- Vectorized: ~0.01s (100x+ faster) ⭐

**When to use each**:
- Vectorized: When operation can be done on entire columns
- `apply()`: When you need row-wise string formatting or complex logic
- Never use `iterrows()`: Always has better alternatives

### 2. File System Operations

**❌ AVOID: Multiple directory traversals**
```python
# SLOW - Walks directory tree twice
manifest_files = find_manifest_files("capsules/")
markdown_files = find_markdown_files("capsules/")
```

**✅ PREFER: Single traversal with multiple filters**
```python
# FASTER - Single walk with multiple collectors
manifest_files, markdown_files = scan_directory_once("capsules/")
```

**Performance Impact**: Reduces I/O operations by 50% or more when scanning large directory trees.

### 3. String Concatenation

**❌ AVOID: Repeated string concatenation in loops**
```python
# SLOW - Creates new string object on each iteration
html = ""
for item in items:
    html += f"<div>{item}</div>"
```

**✅ PREFER: List comprehension + join**
```python
# FASTER - Builds list then joins once
html_parts = [f"<div>{item}</div>" for item in items]
html = ''.join(html_parts)
```

**Performance Impact**: 2-10x faster for large iterations due to reduced memory allocation.

### 4. Matplotlib Backend

**✅ ALWAYS: Set backend before importing pyplot**
```python
import matplotlib
matplotlib.use("Agg")  # Set backend first
import matplotlib.pyplot as plt
```

**Why**: Prevents GUI backend initialization which is slow and causes issues in headless environments.

## Applied Optimizations

### vault_narrator.py (Runs Hourly)
- **Before**: Used `iterrows()` for 20-row table generation
- **After**: Uses `apply(axis=1)` with lambda function
- **Benefit**: 2x faster for table generation (benchmarked: 1.04s → 0.52s per 1000 iterations)

### capsule_index_job.py (Runs Daily)
- **Before**: Two separate `os.walk()` calls for same directory
- **After**: Single `os.walk()` collecting both file types
- **Benefit**: ~50% reduction in file system I/O operations

### generate_dashboard.py (Runs Daily)
- **Before**: String concatenation in nested loops for HTML generation
- **After**: List collection + single join operation
- **Benefit**: ~3x faster HTML generation for large capsule counts

## Monitoring Performance

### Timing Script Execution

Add timing to scripts that run frequently:

```python
import time
from datetime import datetime

def main():
    start_time = time.time()
    
    # Your code here
    
    elapsed = time.time() - start_time
    print(f"Execution time: {elapsed:.2f} seconds")
```

### GitHub Actions Workflow Timing

Check workflow execution times:
```bash
gh run list --workflow=vault_narrator.yml --limit 10
```

## When to Optimize

1. **Scripts running hourly or more frequently** - Always optimize
2. **Scripts processing large datasets** (>10k rows) - Strongly recommended
3. **Scripts with nested loops** - Review for optimization opportunities
4. **One-time analysis scripts** - Optimization optional

## Anti-patterns to Avoid

1. **Never** use `os.system()` or `subprocess.run()` for simple file operations
2. **Never** read the same file multiple times in one script run
3. **Avoid** nested pandas operations when vectorization is possible
4. **Avoid** loading entire large files into memory when streaming is viable

## Testing Optimizations

Always verify that optimizations:
1. Produce identical output to original code
2. Handle edge cases correctly
3. Don't introduce new dependencies
4. Actually improve performance (measure before/after)

## Resources

- [Pandas Performance](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Profiling Python Code](https://docs.python.org/3/library/profile.html)

---

**Last Updated**: 2026-01-08  
**Maintained By**: LUFT Portal Team
