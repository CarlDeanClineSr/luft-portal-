#!/usr/bin/env python3
"""
Repository Knowledge Index Builder — v2
Scans the full LUFT Portal repo and builds a clean, searchable index.
Now handles JSON reports, physics keywords, timestamps, and better previews.

Author: LUFT Portal System (updated by Grok for Carl Dean Cline Sr.)
Usage: python3 scripts/build_repo_knowledge_v2.py
"""

import os
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Optional TF-IDF
SKLEARN_AVAILABLE = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

# Expanded scan paths (covers everything in your repo)
SCAN_PATHS = [
    ".", "docs", "papers", "results", "figures", "data", "reports",
    "capsules", "analyses", "scripts", "constants", "measurements",
]

# File patterns
TEXT_PATTERNS = ["*.md", "*.txt"]
CSV_PATTERN = "*.csv"
JSON_PATTERN = "*.json"

# Exclusions
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}
EXCLUDE_FILES = {"index.json", "KNOWLEDGE_INDEX.md", "KNOWLEDGE_INDEX_v2.md"}

# Output
OUTPUT_JSON = "data/knowledge/index.json"
OUTPUT_MD = "docs/KNOWLEDGE_INDEX_v2.md"

MAX_PREVIEW_LEN = 300
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Physics boost terms
PHYSICS_BOOST = {"chi", "χ", "f_ring", "mode 8", "attractor", "substrate", "vacuum", "cme", "psp", "luft", "cline"}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_FILES:
        return True
    if path.suffix.lower() in {".wav", ".h5", ".mp4", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
        return True
    return False


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return "error"


def get_last_modified(filepath: Path) -> str:
    try:
        return datetime.fromtimestamp(filepath.stat().st_mtime).astimezone().isoformat()
    except Exception:
        return "unknown"


def extract_title(content: str, filename: str) -> str:
    lines = content.strip().split("\n")
    for line in lines[:30]:
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
        if line.startswith("title:") or line.startswith("Title:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return filename.replace("_", " ").title()


def extract_preview(content: str) -> str:
    lines = content.strip().split("\n")
    # Skip YAML frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                start = i + 1
                break
    preview = " ".join([line.strip() for line in lines[start:start+15] if line.strip()])
    if len(preview) > MAX_PREVIEW_LEN:
        return preview[:MAX_PREVIEW_LEN] + "..."
    return preview


def extract_keywords(content: str, n_keywords: int = 8) -> List[str]:
    # Simple frequency + physics boost
    words = re.findall(r'\b[a-z0-9_χ]{3,}\b', content.lower())
    word_freq = {}
    for w in words:
        if w in PHYSICS_BOOST:
            word_freq[w] = word_freq.get(w, 0) + 10  # boost
        elif len(w) >= 3:
            word_freq[w] = word_freq.get(w, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:n_keywords]]


def index_text_file(filepath: Path, repo_root: Path) -> Dict:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        rel_path = str(filepath.relative_to(repo_root))
        return {
            "path": rel_path,
            "name": filepath.name,
            "kind": "text",
            "title": extract_title(content, filepath.name),
            "preview": extract_preview(content),
            "line_count": len(content.split("\n")),
            "size_bytes": filepath.stat().st_size,
            "last_modified": get_last_modified(filepath),
            "sha256": compute_sha256(filepath),
            "keywords": extract_keywords(content),
            "indexed_at": datetime.now().astimezone().isoformat()
        }
    except Exception as e:
        return {"path": str(filepath.relative_to(repo_root)), "error": str(e)}


def index_csv_file(filepath: Path, repo_root: Path) -> Dict:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        headers = [h.strip() for h in lines[0].split(",")] if lines else []
        return {
            "path": str(filepath.relative_to(repo_root)),
            "name": filepath.name,
            "kind": "csv",
            "title": filepath.stem.replace("_", " ").title(),
            "headers": headers[:10],
            "line_count": len(lines),
            "size_bytes": filepath.stat().st_size,
            "last_modified": get_last_modified(filepath),
            "sha256": compute_sha256(filepath),
            "indexed_at": datetime.now().astimezone().isoformat()
        }
    except Exception as e:
        return {"path": str(filepath.relative_to(repo_root)), "error": str(e)}


def index_json_file(filepath: Path, repo_root: Path) -> Dict:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        preview = json.dumps(data, indent=2)[:MAX_PREVIEW_LEN] + "..." if isinstance(data, dict) else str(data)[:MAX_PREVIEW_LEN]
        return {
            "path": str(filepath.relative_to(repo_root)),
            "name": filepath.name,
            "kind": "json",
            "title": filepath.stem.replace("_", " ").title(),
            "preview": preview,
            "size_bytes": filepath.stat().st_size,
            "last_modified": get_last_modified(filepath),
            "sha256": compute_sha256(filepath),
            "keywords": ["json", "report", "chi", "luft"] + extract_keywords(str(data)),
            "indexed_at": datetime.now().astimezone().isoformat()
        }
    except Exception as e:
        return {"path": str(filepath.relative_to(repo_root)), "error": str(e)}


def scan_repository(repo_root: Path) -> List[Dict]:
    indexed_files = []
    for scan_path in SCAN_PATHS:
        search_dir = repo_root / scan_path
        if not search_dir.exists():
            continue
        # Text & Markdown
        for pattern in TEXT_PATTERNS:
            for filepath in search_dir.rglob(pattern):
                if should_skip(filepath) or filepath.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
                entry = index_text_file(filepath, repo_root)
                indexed_files.append(entry)
        # CSV
        for filepath in search_dir.rglob(CSV_PATTERN):
            if should_skip(filepath) or filepath.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            entry = index_csv_file(filepath, repo_root)
            indexed_files.append(entry)
        # JSON reports
        for filepath in search_dir.rglob(JSON_PATTERN):
            if should_skip(filepath) or filepath.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            entry = index_json_file(filepath, repo_root)
            indexed_files.append(entry)
    indexed_files.sort(key=lambda x: x.get("path", ""))
    return indexed_files


def write_json_index(indexed_files: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    index_data = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "total_files": len(indexed_files),
        "files": indexed_files
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON index written: {output_path} ({len(indexed_files)} files)")


def write_markdown_index(indexed_files: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# LUFT Repository Knowledge Index — v2",
        f"**Generated:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"**Total Files Indexed:** {len(indexed_files)}",
        "",
        "---",
        ""
    ]
    for entry in indexed_files:
        path = entry.get("path", "")
        title = entry.get("title", entry.get("name", "Untitled"))
        preview = entry.get("preview", "")[:200] + "..." if entry.get("preview") else ""
        lines.append(f"### [{title}]({path})")
        lines.append(f"**Path:** `{path}`  ")
        if preview:
            lines.append(f"**Preview:** {preview}")
        lines.append("")
    lines.append("---")
    lines.append("*Auto-generated by `scripts/build_repo_knowledge_v2.py`*")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"✅ Markdown index written: {output_path}")


def main():
    print("🔍 LUFT Repository Knowledge Index Builder — v2")
    print("=" * 70)
    repo_root = Path(__file__).resolve().parent.parent
    print(f"Repository root: {repo_root}")
    print()

    print("Scanning repository...")
    indexed_files = scan_repository(repo_root)
    print(f"Found and indexed {len(indexed_files)} files")

    json_path = repo_root / OUTPUT_JSON
    md_path = repo_root / OUTPUT_MD

    write_json_index(indexed_files, json_path)
    write_markdown_index(indexed_files, md_path)

    print("\n✅ Knowledge index update complete!")
    print("   Run this script daily via GitHub Actions or manually.")


if __name__ == "__main__":
    main()
