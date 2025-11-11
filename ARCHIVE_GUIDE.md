```markdown
# LUFT Archive Guide

Purpose
This guide explains the archive layout and how to find, request, and cite raw data and historic materials that are not present in the Portal.

Top-level organization
- /recordings — all raw WAV/SDR recordings (large files). These are managed with Git LFS or mirrored to Zenodo as needed.
- /data — instrument logs, CSVs, experimental outputs
- /notes — historic text documents and chat logs
- /notebooks_raw — older notebooks and full analyses (may reference many data files)
- metadata_master_list.csv — master index of archive entries (use this as your search starting point)
- /capsules_archive — older capsules not in the portal

How to request a subset of the archive
1. Search metadata_master_list.csv for the id or file names you need.
2. Open an Issue in the Portal repository with label `data-request` and include:
   - capsule id or file path
   - intended use / reproduction steps
   - desired delivery format (download link, Zenodo DOI, or partial extraction)
3. Archive maintainers will prepare a package (tar.gz) and publish via Zenodo if necessary. For very large datasets, we will provide an S3 presigned URL.

Citation and DOIs
- When we publish any dataset snapshot to Zenodo, it will get a DOI. Please cite the DOI and the capsule id when publishing results.

Large file handling
- For files larger than ~50 MB we use Git LFS or external archiving.
- If you plan to add new WAV recordings, ask for a LFS quota or upload to Zenodo/S3 and add the link to the metadata table.

Snapshot policy
- We create a snapshot of the archive monthly and tag it `archive-YYYY-MM`.
- If you need reproducibility for a paper, cite the snapshot tag or DOI.

Governance
- Archive requests are triaged weekly. If your request is urgent (review or replication deadline), mark the issue with `priority:high`.

Contact & support
- Open an issue with label `archive-support` or email (if provided) to request faster handling.
```
