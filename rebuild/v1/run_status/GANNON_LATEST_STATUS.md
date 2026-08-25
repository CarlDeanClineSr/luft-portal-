# CLINE L1 Gannon DSCOVR Magnetic Run Status

- Verdict: **FAIL**
- Install outcome: `success`
- Test outcome: `success`
- Historical outcome: `failure`
- Historical exit code: `1`
- Run name: `gannon_may_2024_dscovr_mag_only`
- Run ID: `32911369128`
- Commit tested: `13438bebaae6d8ea6c27476d6b3cca5d44d4d4e7`
- Analysis protocol: `CLINE-L1-B24M-TRAIL-v1`
- Ingest protocol: `CDAWEB-DSCOVR-RESTCSV-1M-v1`
- Source dataset: `DSCOVR_H0_MAG`
- Paired plasma: `false`
- Completed UTC: `2026-08-25T23:35:47Z`

## Output files
```text
RUN_EXIT_CODE.txt	2 bytes
RUN_LOG.txt	1785 bytes
download/raw/magnetic/dscovr_h0_mag_20240507T0000_20240508T0000.csv	5296404 bytes
download/raw/magnetic/dscovr_h0_mag_20240507T0000_20240508T0000.descriptor.json	1200 bytes
```

## Run log tail
```text
Traceback (most recent call last):
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 212, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 206, in main
    result = run_named(args.config, args.run, args.outdir)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 186, in run_named
    result = run_magnetic_only(name, spec, root, warmup)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 87, in run_magnetic_only
    mag_path, mag_summary = download_magnetic_interval(
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/download_dscovr_cdaweb.py", line 476, in download_magnetic_interval
    raw = normalize_magnetic_csv(read_cdaweb_csv(csv_bytes), config)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/download_dscovr_cdaweb.py", line 352, in normalize_magnetic_csv
    bx_col, by_col, bz_col = _find_vector_columns(raw, "B1GSE")
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/download_dscovr_cdaweb.py", line 313, in _find_vector_columns
    raise DownloadError(f"vector variable {base!r} has fewer than 3 columns: {candidates}")
historical.download_dscovr_cdaweb.DownloadError: vector variable 'B1GSE' has fewer than 3 columns: []
```
