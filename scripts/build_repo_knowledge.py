#!/usr/bin/env python3
"""
LUFT Knowledge Index — v3
Imperial-style repo scanner. 
No bloat. Just indexes what matters and spits out clean JSON + MD.
For Carl Dean Cline Sr. — Imperial Physics Observatory
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent

SCAN_PATHS = [".", "docs", "papers", "results", "reports", "capsules", "analyses", "data", "scripts"]
TEXT_EXT = {".md", ".txt"}
JSON_EXT = {".json"}
CSV_EXT = {".csv"}

EXCLUDE = {".git", ".github", "__pycache__", "venv", ".venv", "node_modules"}

MAX_PREVIEW = 300


def hash_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_preview(p: Path) -> str:
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(MAX_PREVIEW * 5)
        # Remove YAML frontmatter if present
        if text.startswith("---"):
            text = text.split("---", 2)[-1]
        return text[:MAX_PREVIEW].replace("\n", " ").strip() + ("..." if len(text) > MAX_PREVIEW else "")
    except:
        return ""


def index_file(p: Path) -> dict:
    rel = str(p.relative_to(REPO_ROOT))
    stat = p.stat()
    return {
        "path": rel,
        "name": p.name,
        "kind": p.suffix.lower().lstrip(".") or "unknown",
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "sha256": hash_file(p),
        "preview": get_preview(p) if p.suffix.lower() in TEXT_EXT | JSON_EXT else "",
        "indexed": datetime.now().astimezone().isoformat()
    }


def build_index():
    print("🔍 Building LUFT Knowledge Index v3 — Imperial style")
    files = []

    for path_str in SCAN_PATHS:
        for item in (REPO_ROOT / path_str).rglob("*"):
            if any(ex in item.parts for ex in EXCLUDE):
                continue
            if item.is_file() and item.suffix.lower() in TEXT_EXT | JSON_EXT | CSV_EXT:
                if item.stat().st_size > 10_000_000:  # 10 MB skip
                    continue
                files.append(index_file(item))

    files.sort(key=lambda x: x["path"])

    # JSON
    index_data = {
        "generated": datetime.now().astimezone().isoformat(),
        "total": len(files),
        "files": files
    }
    json_out = REPO_ROOT / "data/knowledge/index.json"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    print(f"✅ JSON index → {json_out} ({len(files)} files)")

    # Simple Markdown
    md_out = REPO_ROOT / "docs/KNOWLEDGE_INDEX_v3.md"
    lines = ["# LUFT Knowledge Index v3", f"Generated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}", f"Total files: {len(files)}", "", "---", ""]
    for f in files:
        lines.append(f"**{f['name']}**  ")
        lines.append(f"`{f['path']}`  ")
        if f.get("preview"):
            lines.append(f"Preview: {f['preview']}")
        lines.append("")
    md_out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Markdown index → {md_out}")

    print("Done. Index is fresh and distinct.")


if __name__ == "__main__":
    build_index()
