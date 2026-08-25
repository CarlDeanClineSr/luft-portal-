# CLINE L1 Gannon Storm Run Status

- Verdict: **FAIL**
- Install outcome: `success`
- Test outcome: `success`
- Historical outcome: `failure`
- Historical exit code: `1`
- Run ID: `32900139350`
- Commit tested: `f6e1fe69b971aa44b3478ad5f86bab3459e4e7ca`
- Analysis protocol: `CLINE-L1-B24M-TRAIL-v1`
- Ingest protocol: `CDAWEB-DSCOVR-1M-MEAN-v1`
- Completed UTC: `2026-08-25T21:18:06Z`

## Output files
```text
RUN_EXIT_CODE.txt	2 bytes
RUN_LOG.txt	664 bytes
```

## Run log tail
```text
Traceback (most recent call last):
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 182, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 176, in main
    result = run_named(args.config, args.run, args.outdir)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/luft-portal-/luft-portal-/rebuild/v1/historical/run_epoch_batch.py", line 149, in run_named
    raise KeyError(f"run {name!r} is not defined")
KeyError: "run 'gannon_storm_may_2024' is not defined"
```
