#!/usr/bin/env python3
"""
evidence_extractor.py
=====================
LUFT Portal — Priority Evidence Package Extractor
Author: Carl Dean Cline Sr.
Date:   2026-05-14

PURPOSE
-------
Scans repository files and git history for evidence related to three
priority evidence packages:

  Package A: 122,079 Observations → G = 6.6667e-11 and 20.55 Hz Ring Frequency
  Package B: Mode 8 Fractures and CME Attractor Spikes
  Package C: chi=0.15 Boundary and Seismic Event Correlations

Supports incremental processing via a checkpoint file so repeated runs only
process new commits and files.  Outputs structured JSON and Markdown reports.

USAGE
-----
  python evidence_extractor.py
  python evidence_extractor.py --output-dir results/evidence_packages
  python evidence_extractor.py --max-commits 1000
  python evidence_extractor.py --packages A B
  python evidence_extractor.py --reset-checkpoint
  python evidence_extractor.py --files-only
  python evidence_extractor.py --commits-only

OUTPUTS
-------
  results/evidence_packages/evidence_package_A.json
  results/evidence_packages/evidence_package_B.json
  results/evidence_packages/evidence_package_C.json
  results/evidence_packages/ALL_EVIDENCE.json
  results/evidence_packages/EVIDENCE_SUMMARY.md
  results/evidence_packages/.checkpoint.json   (not committed to git)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Evidence package definitions
# ---------------------------------------------------------------------------

EVIDENCE_PACKAGES: dict = {
    "A": {
        "title": "122,079 Observations → G = 6.6667×10⁻¹¹ and 20.55 Hz Ring Frequency",
        "description": (
            "Evidence linking 122,079 real-world stress observations to the "
            "derivation of Newton's gravitational constant G and the 20.55 Hz "
            "vacuum-integrity ring frequency via the chi-VSK pipeline."
        ),
        "patterns": [
            r"122[,\s]?079",
            r"6\.6667[eE]-?11",
            r"6\.6667\s*[x×*]\s*10",
            r"20\.55\s*[Hh][Zz]",
            r"20\.554",
            r"20\.556",
            r"20\.5556",
            r"ring\s*frequency",
            r"chi[_\-\s]?VSK",
            r"chi[_\-/]alpha",
            r"[Rr]oute\s*3[Bb]",
            r"ROUTE_3B",
            r"G_derived",
            r"VSK\s*pipeline",
            r"1\s*/\s*chi",
            r"chi_to_G",
            r"f_ring",
        ],
        "key_terms": [
            "122,079", "6.6667e-11", "20.55 Hz", "chi-VSK",
            "ring frequency", "Route 3B", "G_derived",
        ],
    },
    "B": {
        "title": "Mode 8 Fractures and CME Attractor Spikes",
        "description": (
            "Evidence for Mode 8 substrate fractures and CME attractor spikes "
            "visible in raw telemetry, including baseline, onset, peak, and "
            "ringdown windows."
        ),
        "patterns": [
            r"[Mm]ode\s*8",
            r"mode_8",
            r"MODE_8",
            r"[Ff]racture",
            r"CME\s*attractor",
            r"attractor\s*spike",
            r"attractor\s*state",
            r"[Hh]eartbeat",
            r"[Hh]armonic",
            r"[Rr]ing.?down",
            r"ringdown",
            r"[Ff]ractal\s*echo",
            r"momentum\s*recoil",
            r"CME\s*heartbeat",
            r"harmonic_mode",
            r"detect_harmonic",
            r"attractor_pct",
            r"[Ff]oam\s*bubble",
            r"vacuum\s*fracture",
        ],
        "key_terms": [
            "Mode 8", "fracture", "CME attractor", "attractor spike",
            "heartbeat", "harmonic", "ringdown", "fractal echo",
        ],
    },
    "C": {
        "title": "chi=0.15 Boundary and Seismic Event Correlations",
        "description": (
            "Evidence connecting chi=0.15 magnetic-medium boundary-hit events "
            "(ACE/DSCOVR telemetry) to seismic events from USGS, testing "
            "cross-scale structural correlation."
        ),
        "patterns": [
            r"chi\s*=\s*0\.15",
            r"chi_amplitude",
            r"AT_BOUNDARY",
            r"[Ss]eismic",
            r"[Ee]arthquake",
            r"\bUSGS\b",
            r"\bDSCOVR\b",
            r"\bACE\b",
            r"[Tt]emporal\s*corr",
            r"boundary\s*hit",
            r"chi\s*boundary",
            r"chi_limit",
            r"CHI_LIMIT",
            r"CHI_015",
            r"seismic.*chi",
            r"chi.*seismic",
            r"precursor.*law",
        ],
        "key_terms": [
            "chi=0.15", "AT_BOUNDARY", "chi_amplitude",
            "seismic", "earthquake", "USGS", "DSCOVR", "ACE",
            "temporal correlation",
        ],
    },
}

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# File extensions to scan for text content
TEXT_EXTENSIONS: set = {
    ".py", ".md", ".txt", ".yml", ".yaml", ".sh",
    ".html", ".js", ".ts", ".rst", ".tex",
}

# Data files — scanned only when small enough
DATA_EXTENSIONS: set = {".json", ".csv"}

# Per-category size limits (bytes)
MAX_TEXT_SIZE = 100 * 1024      # 100 KB — catches all source / docs
MAX_DATA_SIZE = 50 * 1024       # 50 KB  — small data files only

# Snippet context window (chars around each match)
SNIPPET_CONTEXT = 180

# Maximum stored entries per package
MAX_ENTRIES_PER_PACKAGE = 2000

# Progress print every N files
PROGRESS_INTERVAL = 1000

# Max commits processed per run
DEFAULT_MAX_COMMITS = 500


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def truncate(text: str, limit: int = 400) -> str:
    return text[:limit] + "…" if len(text) > limit else text


def snippet(content: str, start: int, end: int) -> str:
    lo = max(0, start - SNIPPET_CONTEXT)
    hi = min(len(content), end + SNIPPET_CONTEXT)
    raw = content[lo:hi].replace("\n", " ").replace("\r", "")
    raw = re.sub(r" {2,}", " ", raw).strip()
    return truncate(raw, 400)


def run_git(args: list, cwd: Path, timeout: int = 120) -> str:
    """Run a git command; return stdout or '' on failure."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def is_binary(path: Path) -> bool:
    try:
        return b"\x00" in path.read_bytes()[:8192]
    except OSError:
        return True


def compile_patterns(pkg_id: str) -> list:
    """Return list of (pattern_str, compiled_regex) for a package."""
    out = []
    for p in EVIDENCE_PACKAGES[pkg_id]["patterns"]:
        try:
            out.append((p, re.compile(p, re.IGNORECASE | re.MULTILINE)))
        except re.error as e:
            print(f"  [WARN] bad pattern '{p}': {e}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def load_checkpoint(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return {"last_commit_sha": None, "runs": 0, "created_at": utcnow()}


def save_checkpoint(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), "utf-8")


# ---------------------------------------------------------------------------
# File scanner — current working tree
# ---------------------------------------------------------------------------

def scan_files(
    repo_path: Path,
    packages: list,
    compiled: dict,
    output_dir: Path,
) -> dict:
    """
    Enumerate tracked files via ``git ls-files`` and search for patterns.
    Uses ``git ls-files`` so the .git dir is excluded and .gitignore is
    respected; this is orders-of-magnitude faster than rglob on large repos.
    """
    results = {p: [] for p in packages}
    scanned = skipped = matched_files = 0

    raw = run_git(
        ["ls-files", "--cached", "--others", "--exclude-standard"],
        repo_path,
        timeout=30,
    )
    tracked = [l for l in raw.splitlines() if l.strip()]

    print(f"  {len(tracked)} tracked files to consider …")

    for rel in tracked:
        fpath = repo_path / rel
        ext = Path(rel).suffix.lower()

        if ext in TEXT_EXTENSIONS:
            size_limit = MAX_TEXT_SIZE
        elif ext in DATA_EXTENSIONS:
            size_limit = MAX_DATA_SIZE
        else:
            continue  # not a scannable type

        # Skip the live output dir to avoid self-referential hits
        try:
            fpath.relative_to(output_dir)
            continue
        except ValueError:
            pass

        if not fpath.is_file():
            continue

        try:
            if fpath.stat().st_size > size_limit:
                skipped += 1
                continue
        except OSError:
            continue

        if is_binary(fpath):
            continue

        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        scanned += 1
        if scanned % PROGRESS_INTERVAL == 0:
            print(f"    … {scanned} files scanned, {matched_files} matched")

        file_matched = False
        for pkg in packages:
            if len(results[pkg]) >= MAX_ENTRIES_PER_PACKAGE:
                continue
            for pat_str, pat in compiled[pkg]:
                m = pat.search(content)
                if m:
                    line_num = content.count("\n", 0, m.start()) + 1
                    results[pkg].append({
                        "source": "file",
                        "category": pkg,
                        "file_path": rel,
                        "line": line_num,
                        "matched_term": m.group(0),
                        "matched_pattern": pat_str,
                        "snippet": snippet(content, m.start(), m.end()),
                        "commit_sha": None,
                        "commit_timestamp": None,
                        "scanned_at": utcnow(),
                    })
                    file_matched = True

        if file_matched:
            matched_files += 1

    print(
        f"  File scan done: {scanned} read, {matched_files} matched, "
        f"{skipped} skipped (over size limit)"
    )
    return results


# ---------------------------------------------------------------------------
# Git history scanner — incremental, commit-message grep only
# ---------------------------------------------------------------------------

def _git_log_grep(
    repo_path: Path,
    term: str,
    since_sha: str | None,
    max_count: int,
) -> list:
    """
    Use ``git log --grep`` to find commits whose *message* contains TERM.
    Returns list of (sha, timestamp, subject).

    This is fast even over 50,000+ commits because git only reads commit
    metadata, not diff content.
    """
    args = [
        "log",
        "--format=%H\t%aI\t%s",
        f"--grep={term}",
        "--regexp-ignore-case",
        f"--max-count={max_count}",
    ]
    if since_sha:
        args.append(f"{since_sha}..HEAD")
    raw = run_git(args, repo_path, timeout=30)
    rows = []
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            rows.append(tuple(parts))
    return rows


def _get_changed_files(repo_path: Path, sha: str) -> list:
    """
    Return list of filenames changed in commit SHA.
    Uses --name-only --diff-filter=AM with a short timeout.
    Falls back to [] on timeout (avoids blocking on large merge commits).
    """
    raw = run_git(
        ["diff-tree", "--no-commit-id", "-r", "--name-only", "--diff-filter=AM", sha],
        repo_path,
        timeout=5,
    )
    return [l.strip() for l in raw.splitlines() if l.strip()]


def scan_git_history(
    repo_path: Path,
    packages: list,
    compiled: dict,
    checkpoint: dict,
    max_commits: int,
) -> tuple:
    """
    Scan git history incrementally using ``git log --grep`` on commit messages.
    Pickaxe (diff-content) search is intentionally skipped: it stalls on large
    bulk-import commits.  File content is already covered by scan_files().

    Returns (results_dict, latest_sha_seen).
    """
    results = {p: [] for p in packages}
    since_sha = checkpoint.get("last_commit_sha")

    head_sha = run_git(["rev-parse", "HEAD"], repo_path).strip()
    if not head_sha:
        print("  Cannot determine HEAD SHA — skipping git history scan.")
        return results, since_sha

    if since_sha == head_sha:
        print(f"  Already at HEAD ({head_sha[:8]}), nothing new.")
        return results, head_sha

    # Per-package commit budget (split evenly across packages)
    per_pkg = max(20, max_commits // len(packages))

    all_shas_seen: set = set()

    for pkg in packages:
        pkg_count = 0

        for term in EVIDENCE_PACKAGES[pkg]["key_terms"]:
            if pkg_count >= per_pkg:
                break
            rows = _git_log_grep(repo_path, term, since_sha, per_pkg)
            for sha, ts, subj in rows:
                if sha in all_shas_seen:
                    continue
                all_shas_seen.add(sha)

                # Find the first compiled pattern that matches the full message
                full_msg = run_git(
                    ["log", "--format=%B", "-1", sha], repo_path, timeout=5
                )
                text = (full_msg or subj).strip()

                matched = False
                for pat_str, pat in compiled[pkg]:
                    m = pat.search(text)
                    if m:
                        results[pkg].append({
                            "source": "commit_message",
                            "category": pkg,
                            "file_path": None,
                            "line": None,
                            "matched_term": m.group(0),
                            "matched_pattern": pat_str,
                            "snippet": snippet(text, m.start(), m.end()),
                            "commit_sha": sha,
                            "commit_timestamp": ts,
                            "scanned_at": utcnow(),
                        })
                        matched = True
                        break

                # Also record filenames changed in this commit (if any match)
                if matched:
                    for fpath in _get_changed_files(repo_path, sha):
                        ext = Path(fpath).suffix.lower()
                        if ext not in (TEXT_EXTENSIONS | DATA_EXTENSIONS):
                            continue
                        for pat_str, pat in compiled[pkg]:
                            if pat.search(fpath):
                                results[pkg].append({
                                    "source": "commit_file",
                                    "category": pkg,
                                    "file_path": fpath,
                                    "line": None,
                                    "matched_term": term,
                                    "matched_pattern": pat_str,
                                    "snippet": truncate(
                                        f"[{sha[:8]}] {subj} | {fpath}", 400
                                    ),
                                    "commit_sha": sha,
                                    "commit_timestamp": ts,
                                    "scanned_at": utcnow(),
                                })
                                break

                pkg_count += 1
                if pkg_count >= per_pkg:
                    break

        print(f"  Package {pkg}: {pkg_count} commit-message hits")

    return results, head_sha


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def dedup_merge(existing: list, new_entries: list) -> list:
    """Merge new entries into existing, de-duplicating by key tuple."""
    seen = {
        (e.get("source"), e.get("file_path"),
         e.get("matched_pattern"), e.get("commit_sha"))
        for e in existing
    }
    for e in new_entries:
        key = (e.get("source"), e.get("file_path"),
               e.get("matched_pattern"), e.get("commit_sha"))
        if key not in seen:
            existing.append(e)
            seen.add(key)
    return existing[:MAX_ENTRIES_PER_PACKAGE]


def load_existing(json_path: Path) -> list:
    if json_path.exists():
        try:
            return json.loads(json_path.read_text("utf-8")).get("entries", [])
        except Exception:
            pass
    return []


def write_pkg_json(path: Path, pkg_id: str, entries: list) -> None:
    info = EVIDENCE_PACKAGES[pkg_id]
    path.write_text(
        json.dumps({
            "package": pkg_id,
            "title": info["title"],
            "description": info["description"],
            "key_terms": info["key_terms"],
            "generated_at": utcnow(),
            "total_entries": len(entries),
            "entries": entries,
        }, indent=2, ensure_ascii=False),
        "utf-8",
    )


def write_all_json(output_dir: Path, all_results: dict) -> None:
    combined = []
    for entries in all_results.values():
        combined.extend(entries)
    (output_dir / "ALL_EVIDENCE.json").write_text(
        json.dumps({
            "generated_at": utcnow(),
            "total_entries": len(combined),
            "packages": list(all_results.keys()),
            "entries": combined,
        }, indent=2, ensure_ascii=False),
        "utf-8",
    )
    print(f"  ALL_EVIDENCE.json: {len(combined)} entries")


def write_summary_md(output_dir: Path, all_results: dict, checkpoint: dict) -> None:
    lines = [
        "# LUFT Engine Priority Evidence Report",
        "",
        f"**Generated:** {utcnow()}  ",
        f"**Last commit processed:** `{checkpoint.get('last_commit_sha', 'N/A')}`  ",
        f"**Total extraction runs:** {checkpoint.get('runs', 0)}  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Package | Title | Entries |",
        "|---------|-------|---------|",
    ]
    for pkg_id, entries in all_results.items():
        title = EVIDENCE_PACKAGES[pkg_id]["title"]
        lines.append(f"| **{pkg_id}** | {title} | {len(entries)} |")

    lines += ["", "---", ""]

    for pkg_id, entries in all_results.items():
        info = EVIDENCE_PACKAGES[pkg_id]
        lines += [
            f"## Package {pkg_id}: {info['title']}",
            "",
            f"_{info['description']}_",
            "",
            f"**Search terms:** {', '.join(f'`{t}`' for t in info['key_terms'])}  ",
            f"**Total entries:** {len(entries)}",
            "",
        ]
        if entries:
            shown = entries[:20]
            lines += [
                "### Top Evidence (up to 20 entries)",
                "",
                "| # | Source | File / Commit | Matched | Snippet |",
                "|---|--------|---------------|---------|---------|",
            ]
            for i, e in enumerate(shown, 1):
                src = e.get("source", "")
                fp = e.get("file_path") or ""
                sha = e.get("commit_sha") or ""
                loc = f"`{fp}`" if fp else ""
                if sha:
                    loc += f" `{sha[:8]}`"
                term = (e.get("matched_term") or "")[:40]
                snip = (e.get("snippet") or "")[:80].replace("|", "\\|")
                lines.append(f"| {i} | {src} | {loc} | `{term}` | {snip} |")
            lines.append("")
        lines += [
            f"**JSON:** [`evidence_package_{pkg_id}.json`]"
            f"(evidence_package_{pkg_id}.json)",
            "",
            "---",
            "",
        ]

    lines += [
        "## How to Run Locally",
        "",
        "```bash",
        "# Default: scan files + 500 most-recent commits",
        "python evidence_extractor.py",
        "",
        "# More commits",
        "python evidence_extractor.py --max-commits 2000",
        "",
        "# Files only (no git history)",
        "python evidence_extractor.py --files-only",
        "",
        "# Specific packages",
        "python evidence_extractor.py --packages A C",
        "",
        "# Full reset and rescan",
        "python evidence_extractor.py --reset-checkpoint",
        "```",
        "",
        "## Incremental Behaviour",
        "",
        "Each run saves `last_commit_sha` in `.checkpoint.json`.  "
        "The next run skips commits already processed, so 50,000+ commit "
        "histories are covered incrementally over multiple scheduled runs.",
    ]

    (output_dir / "EVIDENCE_SUMMARY.md").write_text("\n".join(lines), "utf-8")
    print(f"  EVIDENCE_SUMMARY.md written")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="LUFT Portal — Priority Evidence Package Extractor"
    )
    p.add_argument("--repo-path", default=".",
                   help="Repository root (default: current dir)")
    p.add_argument("--output-dir", default="results/evidence_packages",
                   help="Output directory (default: results/evidence_packages)")
    p.add_argument("--max-commits", type=int, default=DEFAULT_MAX_COMMITS,
                   help=f"Max commits per run (default: {DEFAULT_MAX_COMMITS})")
    p.add_argument("--packages", nargs="+", choices=["A", "B", "C"],
                   default=["A", "B", "C"],
                   help="Packages to extract (default: A B C)")
    p.add_argument("--reset-checkpoint", action="store_true",
                   help="Clear checkpoint and restart from beginning")
    p.add_argument("--files-only", action="store_true",
                   help="Scan files only; skip git history")
    p.add_argument("--commits-only", action="store_true",
                   help="Scan git history only; skip file tree")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    repo_path = Path(args.repo_path).resolve()
    output_dir = (repo_path / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = output_dir / ".checkpoint.json"
    packages = args.packages

    bar = "=" * 62
    print(bar)
    print("LUFT Portal — Evidence Package Extractor")
    print(f"Started     : {utcnow()}")
    print(f"Repo        : {repo_path}")
    print(f"Output      : {output_dir}")
    print(f"Packages    : {', '.join(packages)}")
    print(f"Max commits : {args.max_commits}")
    print(bar)

    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()
        print("Checkpoint cleared.")

    checkpoint = load_checkpoint(checkpoint_path)
    print(f"Checkpoint  : last SHA = {checkpoint.get('last_commit_sha', 'none')}")

    compiled = {pkg: compile_patterns(pkg) for pkg in packages}

    # ---- Phase 1: file tree scan ----------------------------------------
    file_results = {p: [] for p in packages}
    if not args.commits_only:
        print("\n[Phase 1] Scanning current file tree …")
        file_results = scan_files(repo_path, packages, compiled, output_dir)

    # ---- Phase 2: git history scan (incremental) ------------------------
    git_results = {p: [] for p in packages}
    latest_sha = checkpoint.get("last_commit_sha")
    if not args.files_only:
        print("\n[Phase 2] Scanning git history …")
        git_results, latest_sha = scan_git_history(
            repo_path, packages, compiled, checkpoint, args.max_commits
        )

    # ---- Phase 3: merge and write ----------------------------------------
    print("\n[Phase 3] Merging and writing results …")
    all_results: dict = {}
    for pkg in packages:
        existing = load_existing(output_dir / f"evidence_package_{pkg}.json")
        merged = dedup_merge(existing, file_results[pkg] + git_results[pkg])
        all_results[pkg] = merged
        write_pkg_json(output_dir / f"evidence_package_{pkg}.json", pkg, merged)
        print(
            f"  Package {pkg}: {len(file_results[pkg])} file + "
            f"{len(git_results[pkg])} commit → {len(merged)} total"
        )

    write_all_json(output_dir, all_results)
    write_summary_md(output_dir, all_results, checkpoint)

    # ---- Update checkpoint -----------------------------------------------
    checkpoint["last_commit_sha"] = latest_sha
    checkpoint["files_scanned_at"] = utcnow()
    checkpoint["runs"] = checkpoint.get("runs", 0) + 1
    checkpoint["last_run_at"] = utcnow()
    save_checkpoint(checkpoint_path, checkpoint)

    print(f"\nCheckpoint updated: last SHA = {latest_sha}")
    print(f"Done. {utcnow()}")
    print(bar)


if __name__ == "__main__":
    main()
