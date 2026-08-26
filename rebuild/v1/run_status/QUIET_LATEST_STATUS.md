# CLINE L1 Quiet Solar-Minimum Run Status

- Verdict: **FAIL**
- Install outcome: `success`
- Test outcome: `success`
- Historical outcome: `failure`
- Historical exit code: `1`
- Run ID: `32900524648`
- Commit tested: `6c89f522daedfeaaea34d2dda0958dff399992db`
- Selection rule: kinetics only; χ excluded from window selection
- Analysis protocol: `CLINE-L1-B24M-TRAIL-v1`
- Ingest protocol: `CDAWEB-DSCOVR-1M-MEAN-v1`
- Completed UTC: `2026-08-26T00:34:10Z`

## Output files
```text
RUN_EXIT_CODE.txt	2 bytes
RUN_LOG.txt	800 bytes
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
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 179, in run_named
    raise KeyError(f"run {name!r} is not defined; available runs: {available}")
KeyError: "run 'quiet_solar_minimum_scan' is not defined; available runs: ['gannon_may_2024_dscovr_mag_only', 'quiet_dscovr_scan', 'september_2017_dscovr_full']"
```
