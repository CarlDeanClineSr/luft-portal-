#!/usr/bin/env python3
"""
Repository Knowledge Index Builder
Scans key paths and indexes text files, CSVs, and other documents.
Generates data/knowledge/index.json and docs/KNOWLEDGE_INDEX.md

Author: LUFT Portal System
Usage: python3 scripts/build_repo_knowledge.py
"""

import os
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Try to import scikit-learn for TF-IDF keyword extraction (optional)
SKLEARN_AVAILABLE = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

# Paths to scan (relative to repo root)
SCAN_PATHS = [
    ".",
    "docs",
    "papers",
    "results",
    "figures",
    "data",
    "reports",
    "capsules",
    "analyses",
]

# File patterns to index
TEXT_PATTERNS = ["*.md", "*.txt"]
CSV_PATTERN = "*.csv"

# Exclude patterns
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}
EXCLUDE_FILES = {"index.json", "KNOWLEDGE_INDEX.md"}

# Output paths
OUTPUT_JSON = "data/knowledge/index.json"
OUTPUT_MD = "docs/KNOWLEDGE_INDEX.md"

# Maximum preview length
MAX_PREVIEW_LEN = 200

# Maximum file size for indexing (10MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    # Skip excluded directories
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Skip excluded files
    if path.name in EXCLUDE_FILES:
        return True
    
    # Skip binary-like files (WAV, H5, MP4, etc.)
    if path.suffix.lower() in {".wav", ".h5", ".mp4", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
        return True
    
    return False


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"error: {str(e)}"


def extract_title(content: str, filename: str) -> str:
    """Extract title from content (first heading or first line)."""
    lines = content.strip().split("\n")
    
    # Try to find first markdown heading
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    
    # Try to find YAML frontmatter title
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:10], 1):
            if line.strip() == "---":
                break
            if line.startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"\'')
    
    # Use first non-empty line
    for line in lines[:10]:
        line = line.strip()
        if line and not line.startswith("---"):
            # Truncate if too long
            if len(line) > 80:
                return line[:77] + "..."
            return line
    
    # Fallback to filename
    return filename


def extract_preview(content: str) -> str:
    """Extract a preview snippet from content."""
    lines = content.strip().split("\n")
    
    # Skip YAML frontmatter
    start_idx = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                start_idx = i + 1
                break
    
    # Get meaningful content
    preview_lines = []
    for line in lines[start_idx:]:
        line = line.strip()
        # Skip markdown headers and empty lines for preview
        if line and not line.startswith("#"):
            preview_lines.append(line)
        if len(" ".join(preview_lines)) >= MAX_PREVIEW_LEN:
            break
    
    preview = " ".join(preview_lines)
    if len(preview) > MAX_PREVIEW_LEN:
        return preview[:MAX_PREVIEW_LEN] + "..."
    return preview


def extract_keywords_simple(content: str, n_keywords: int = 5) -> List[str]:
    """Extract keywords using simple word frequency (fallback when sklearn not available)."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "this", "that",
        "these", "those", "it", "its", "they", "them", "their"
    }
    
    # Extract words (lowercase, alphanumeric and underscores, min 3 chars)
    words = re.findall(r'\b[a-z0-9_]{3,}\b', content.lower())
    
    # Count word frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:n_keywords]]


def extract_keywords_tfidf(content: str, n_keywords: int = 5) -> List[str]:
    """Extract keywords using TF-IDF (when sklearn is available)."""
    try:
        vectorizer = TfidfVectorizer(
            max_features=n_keywords,
            stop_words='english',
            min_df=1,
            max_df=1.0,
            ngram_range=(1, 2)
        )
        
        # TF-IDF needs multiple documents, so we split into sentences
        sentences = re.split(r'[.!?]\s+', content)
        if len(sentences) < 2:
            # Fallback to simple if not enough sentences
            return extract_keywords_simple(content, n_keywords)
        
        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()
        
        # Get average TF-IDF score for each term
        avg_scores = tfidf_matrix.mean(axis=0).A1
        top_indices = avg_scores.argsort()[-n_keywords:][::-1]
        
        return [feature_names[i] for i in top_indices]
    except Exception:
        return extract_keywords_simple(content, n_keywords)


def extract_keywords(content: str, n_keywords: int = 5) -> List[str]:
    """Extract keywords using TF-IDF if available, otherwise simple frequency."""
    if SKLEARN_AVAILABLE:
        return extract_keywords_tfidf(content, n_keywords)
    else:
        return extract_keywords_simple(content, n_keywords)


def index_text_file(filepath: Path, repo_root: Path) -> Dict:
    """Index a text file (markdown or plain text)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        line_count = len(content.split("\n"))
        file_size = filepath.stat().st_size
        
        # Extract metadata
        title = extract_title(content, filepath.name)
        preview = extract_preview(content)
        keywords = extract_keywords(content, n_keywords=5)
        sha256 = compute_sha256(filepath)
        
        # Get relative path
        rel_path = filepath.relative_to(repo_root)
        
        return {
            "path": str(rel_path),
            "name": filepath.name,
            "kind": "text",
            "title": title,
            "preview": preview,
            "line_count": line_count,
            "size_bytes": file_size,
            "sha256": sha256,
            "keywords": keywords,
            "indexed_at": datetime.now().astimezone().isoformat()
        }
    except Exception as e:
        return {
            "path": str(filepath.relative_to(repo_root)),
            "name": filepath.name,
            "kind": "text",
            "error": str(e)
        }


def index_csv_file(filepath: Path, repo_root: Path) -> Dict:
    """Index a CSV file."""
    import csv
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        line_count = len(lines)
        file_size = filepath.stat().st_size
        
        # Extract headers from first line using CSV parser
        headers = []
        if lines:
            try:
                reader = csv.reader([lines[0]])
                headers = [h.strip() for h in next(reader)]
            except Exception:
                # Fallback to simple split if CSV parsing fails
                headers = [h.strip() for h in lines[0].split(",")]
        
        sha256 = compute_sha256(filepath)
        rel_path = filepath.relative_to(repo_root)
        
        return {
            "path": str(rel_path),
            "name": filepath.name,
            "kind": "csv",
            "title": filepath.stem.replace("_", " ").title(),
            "headers": headers,
            "line_count": line_count,
            "size_bytes": file_size,
            "sha256": sha256,
            "indexed_at": datetime.now().astimezone().isoformat()
        }
    except Exception as e:
        return {
            "path": str(filepath.relative_to(repo_root)),
            "name": filepath.name,
            "kind": "csv",
            "error": str(e)
        }


def scan_repository(repo_root: Path) -> List[Dict]:
    """Scan repository and index all relevant files."""
    indexed_files = []
    
    for scan_path in SCAN_PATHS:
        search_dir = repo_root / scan_path
        if not search_dir.exists():
            continue
        
        # Find text files
        for pattern in TEXT_PATTERNS:
            for filepath in search_dir.rglob(pattern):
                if should_skip(filepath):
                    continue
                
                # Skip very large files
                if filepath.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
                
                entry = index_text_file(filepath, repo_root)
                if entry:
                    indexed_files.append(entry)
        
        # Find CSV files
        for filepath in search_dir.rglob(CSV_PATTERN):
            if should_skip(filepath):
                continue
            
            # Skip very large files (>10MB)
            if filepath.stat().st_size > 10 * 1024 * 1024:
                continue
            
            entry = index_csv_file(filepath, repo_root)
            if entry:
                indexed_files.append(entry)
    
    # Sort by path
    indexed_files.sort(key=lambda x: x.get("path", ""))
    
    return indexed_files


def write_json_index(indexed_files: List[Dict], output_path: Path) -> None:
    """Write the JSON index file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    index_data = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "total_files": len(indexed_files),
        "sklearn_available": SKLEARN_AVAILABLE,
        "files": indexed_files
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Written JSON index: {output_path} ({len(indexed_files)} files)")


def write_markdown_index(indexed_files: List[Dict], output_path: Path) -> None:
    """Write the Markdown summary index."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Group by kind
    by_kind = {}
    for entry in indexed_files:
        kind = entry.get("kind", "unknown")
        if kind not in by_kind:
            by_kind[kind] = []
        by_kind[kind].append(entry)
    
    # Generate markdown
    lines = [
        "# Repository Knowledge Index",
        "",
        f"**Generated:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}  ",
        f"**Total Files Indexed:** {len(indexed_files)}  ",
        f"**TF-IDF Keywords:** {'✓ Enabled (scikit-learn)' if SKLEARN_AVAILABLE else '✗ Disabled (using simple frequency)'}",
        "",
        "---",
        "",
    ]
    
    # Statistics
    lines.append("## Statistics")
    lines.append("")
    for kind, entries in sorted(by_kind.items()):
        lines.append(f"- **{kind.upper()} files:** {len(entries)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # List all files by kind
    for kind, entries in sorted(by_kind.items()):
        lines.append(f"## {kind.upper()} Files ({len(entries)})")
        lines.append("")
        
        if kind == "csv":
            lines.append("| Path | Title | Rows | Headers |")
            lines.append("|------|-------|------|---------|")
            for entry in entries:
                path = entry.get("path", "")
                title = entry.get("title", "")
                line_count = entry.get("line_count", 0)
                headers = entry.get("headers", [])
                header_preview = ", ".join(headers[:3])
                if len(headers) > 3:
                    header_preview += f", ... ({len(headers)} total)"
                lines.append(f"| [{path}]({path}) | {title} | {line_count} | {header_preview} |")
        else:
            lines.append("| Path | Title | Lines | Keywords |")
            lines.append("|------|-------|-------|----------|")
            for entry in entries:
                path = entry.get("path", "")
                title = entry.get("title", "")[:60]
                line_count = entry.get("line_count", 0)
                keywords = entry.get("keywords", [])
                keyword_str = ", ".join(keywords[:3])
                if len(keywords) > 3:
                    keyword_str += ", ..."
                lines.append(f"| [{path}]({path}) | {title} | {line_count} | {keyword_str} |")
        
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This index is auto-generated by `scripts/build_repo_knowledge.py`*  ")
    lines.append("*Updates daily via `.github/workflows/knowledge_index.yml`*")
    lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"✅ Written Markdown index: {output_path}")


def main():
    """Main execution."""
    print("🔍 LUFT Repository Knowledge Index Builder")
    print("=" * 60)
    
    # Get repository root
    repo_root = Path(__file__).resolve().parent.parent
    print(f"Repository root: {repo_root}")
    print(f"TF-IDF keywords: {'✓ ENABLED (scikit-learn)' if SKLEARN_AVAILABLE else '✗ DISABLED (using simple frequency)'}")
    print()
    
    # Scan repository
    print("Scanning repository...")
    indexed_files = scan_repository(repo_root)
    print(f"Found {len(indexed_files)} files to index")
    print()
    
    # Write outputs
    json_path = repo_root / OUTPUT_JSON
    md_path = repo_root / OUTPUT_MD
    
    write_json_index(indexed_files, json_path)
    write_markdown_index(indexed_files, md_path)
    
    print()
    print("=" * 60)
    print("✅ Knowledge index generation complete!")


if __name__ == "__main__":
    main()
