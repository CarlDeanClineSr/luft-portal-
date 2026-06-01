# New Text Documents Intake

This document registers nine newly added repository-root text files as important intake sources for LUFT Portal processing.

## Registered Intake Sources

The engine should treat the following files as active intake material:

- `New Text Document (351).txt`
- `New Text Document (352).txt`
- `New Text Document (353).txt`
- `New Text Document (354).txt`
- `New Text Document (355).txt`
- `New Text Document (356).txt`
- `New Text Document (358).txt`
- `New Text Document (359).txt`
- `New Text Document (360).txt`

## Why They Matter

These files are repository intake sources and should be processed by the engine because they contain a mix of:

- chat backups
- child files
- result captures
- intake material
- test and data notes
- repository processing context

They should not remain as unindexed loose text. The intake flow should read them, summarize them, surface repeated terms and numbers, and write structured outputs for later engine review.

## Commit-Ready Repo Layout

Keep the current layout simple for now:

- source text files remain at the repository root
- intake manifest lives at `configs/new_text_documents_manifest.yaml`
- intake script lives at `scripts/intake_new_text_docs.py`
- markdown output is written to `reports/intake/new_text_documents_summary.md`
- JSON output is written to `results/intake/new_text_documents_index.json`
- automation runs from `.github/workflows/intake-new-text-docs.yml`

## Processing Flow

1. Read the manifest.
2. Read each registered text file from the repository root.
3. Extract a short summary, number metadata, keyword hits, and top words.
4. Write a combined markdown report and JSON index.
5. Upload the generated outputs as workflow artifacts for review.
