#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "new_text_documents_manifest.yaml"
STOP_WORDS = {
    "the", "and", "for", "that", "with", "this", "from", "are", "was", "were", "into", "their",
    "they", "them", "your", "have", "has", "had", "will", "would", "should", "could", "there",
    "about", "what", "when", "where", "which", "while", "than", "then", "also", "just", "like",
    "into", "over", "under", "been", "being", "each", "some", "more", "most", "such", "only",
    "very", "much", "many", "make", "made", "does", "did", "done", "these", "those", "your",
    "you", "our", "out", "not", "but", "all", "any", "can", "its", "it's", "use", "using",
    "new", "text", "document", "documents", "file", "files", "txt",
}
NUMBER_PATTERN = re.compile(r"(?<!\w)[+-]?(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?")
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def safe_read_text(path: Path) -> tuple[str, str | None]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore"), None
    except OSError as exc:
        return "", str(exc)


def summarize_text(text: str, max_chars: int) -> str:
    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not non_empty_lines:
        return ""

    collected: list[str] = []
    current_length = 0
    for line in non_empty_lines[:12]:
        candidate = re.sub(r"\s+", " ", line)
        candidate_length = len(candidate) + (1 if collected else 0)
        if current_length + candidate_length > max_chars:
            break
        collected.append(candidate)
        current_length += candidate_length

    summary = " ".join(collected).strip()
    if len(summary) < max_chars and len(non_empty_lines) > len(collected):
        return f"{summary}..."
    if len(summary) > max_chars:
        return f"{summary[:max_chars - 3].rstrip()}..."
    return summary


def extract_keyword_hits(text: str, keywords: list[str], case_sensitive: bool) -> dict[str, int]:
    flags = 0 if case_sensitive else re.IGNORECASE
    hits: dict[str, int] = {}

    for keyword in keywords:
        pattern = re.escape(keyword)
        if keyword[:1].isalnum():
            pattern = rf"(?<!\w){pattern}"
        if keyword[-1:].isalnum():
            pattern = rf"{pattern}(?!\w)"

        count = len(re.findall(pattern, text, flags=flags))
        if count:
            hits[keyword] = count

    return dict(sorted(hits.items(), key=lambda item: (-item[1], item[0])))


def extract_number_metadata(
    text: str,
    preview_limit: int,
    repeated_limit: int,
) -> dict[str, Any]:
    matches = NUMBER_PATTERN.findall(text)
    counts = Counter(matches)

    numeric_values: list[float] = []
    for match in matches:
        try:
            numeric_values.append(float(match))
        except ValueError:
            continue

    finite_values = [value for value in numeric_values if math.isfinite(value)]

    return {
        "total_matches": len(matches),
        "unique_matches": len(counts),
        "preview": list(counts.keys())[:preview_limit],
        "top_repeated": [
            {"value": value, "count": count}
            for value, count in counts.most_common(repeated_limit)
        ],
        "min_value": min(finite_values) if finite_values else None,
        "max_value": max(finite_values) if finite_values else None,
    }


def extract_top_words(text: str, limit: int) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for word in WORD_PATTERN.findall(text.lower()):
        if len(word) < 3 or word in STOP_WORDS:
            continue
        counter[word] += 1

    return [{"word": word, "count": count} for word, count in counter.most_common(limit)]


def build_document_record(
    root_dir: Path,
    document: dict[str, Any],
    settings: dict[str, Any],
    keywords: list[str],
) -> dict[str, Any]:
    path = root_dir / document["path"]
    exists = path.exists()
    text, error = safe_read_text(path) if exists else ("", "File not found")

    summary_preview_chars = int(settings.get("summary_preview_chars", 600))
    top_words_limit = int(settings.get("top_words_limit", 15))
    numbers_preview_limit = int(settings.get("numbers_preview_limit", 25))
    repeated_numbers_limit = int(settings.get("repeated_numbers_limit", 10))
    case_sensitive = bool(settings.get("keyword_case_sensitive", False))

    return {
        "path": document["path"],
        "type": document.get("type", "unknown"),
        "role": document.get("role", "intake"),
        "enabled": bool(document.get("enabled", True)),
        "exists": exists,
        "error": error,
        "size_bytes": path.stat().st_size if exists else 0,
        "line_count": text.count("\n") + (1 if text else 0),
        "word_count": len(WORD_PATTERN.findall(text)),
        "character_count": len(text),
        "summary": summarize_text(text, summary_preview_chars) if text else "",
        "numbers": extract_number_metadata(text, numbers_preview_limit, repeated_numbers_limit) if text else {
            "total_matches": 0,
            "unique_matches": 0,
            "preview": [],
            "top_repeated": [],
            "min_value": None,
            "max_value": None,
        },
        "keyword_hits": extract_keyword_hits(text, keywords, case_sensitive) if text else {},
        "top_words": extract_top_words(text, top_words_limit) if text else [],
    }


def build_payload(manifest: dict[str, Any], manifest_path: Path, root_dir: Path) -> dict[str, Any]:
    documents = manifest.get("documents", [])
    settings = manifest.get("settings", {})
    keywords = manifest.get("keywords", [])

    records = [
        build_document_record(root_dir, document, settings, keywords)
        for document in documents
        if document.get("enabled", True)
    ]

    aggregate_keyword_hits: Counter[str] = Counter()
    for record in records:
        aggregate_keyword_hits.update(record["keyword_hits"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path.relative_to(root_dir)),
        "documents_processed": len(records),
        "documents": records,
        "aggregate": {
            "total_size_bytes": sum(record["size_bytes"] for record in records),
            "total_word_count": sum(record["word_count"] for record in records),
            "total_number_matches": sum(record["numbers"]["total_matches"] for record in records),
            "aggregate_keyword_hits": dict(sorted(aggregate_keyword_hits.items(), key=lambda item: (-item[1], item[0]))),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# New Text Documents Summary",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Manifest: `{payload['manifest']}`",
        f"- Documents processed: `{payload['documents_processed']}`",
        f"- Total size bytes: `{payload['aggregate']['total_size_bytes']}`",
        f"- Total word count: `{payload['aggregate']['total_word_count']}`",
        f"- Total number matches: `{payload['aggregate']['total_number_matches']}`",
        "",
        "## Aggregate Keyword Hits",
        "",
    ]

    if payload["aggregate"]["aggregate_keyword_hits"]:
        for keyword, count in payload["aggregate"]["aggregate_keyword_hits"].items():
            lines.append(f"- `{keyword}`: {count}")
    else:
        lines.append("- None")

    for record in payload["documents"]:
        lines.extend(
            [
                "",
                f"## {record['path']}",
                "",
                f"- Exists: `{record['exists']}`",
                f"- Type: `{record['type']}`",
                f"- Role: `{record['role']}`",
                f"- Size bytes: `{record['size_bytes']}`",
                f"- Line count: `{record['line_count']}`",
                f"- Word count: `{record['word_count']}`",
                f"- Character count: `{record['character_count']}`",
            ]
        )

        if record["error"]:
            lines.append(f"- Error: `{record['error']}`")

        lines.extend(["", "### Summary", "", record["summary"] or "_No readable content extracted._", "", "### Keyword Hits", ""])
        if record["keyword_hits"]:
            for keyword, count in record["keyword_hits"].items():
                lines.append(f"- `{keyword}`: {count}")
        else:
            lines.append("- None")

        lines.extend(["", "### Top Words", ""])
        if record["top_words"]:
            for item in record["top_words"]:
                lines.append(f"- `{item['word']}`: {item['count']}")
        else:
            lines.append("- None")

        number_metadata = record["numbers"]
        lines.extend(
            [
                "",
                "### Number Metadata",
                "",
                f"- Total matches: `{number_metadata['total_matches']}`",
                f"- Unique matches: `{number_metadata['unique_matches']}`",
                f"- Min value: `{number_metadata['min_value']}`",
                f"- Max value: `{number_metadata['max_value']}`",
                f"- Preview: `{', '.join(number_metadata['preview']) if number_metadata['preview'] else 'None'}`",
                "",
                "### Repeated Numbers",
                "",
            ]
        )
        if number_metadata["top_repeated"]:
            for item in number_metadata["top_repeated"]:
                lines.append(f"- `{item['value']}`: {item['count']}")
        else:
            lines.append("- None")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_intake(manifest_path: Path, root_dir: Path = ROOT) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    settings = manifest.get("settings", {})
    payload = build_payload(manifest, manifest_path, root_dir)

    output_markdown = root_dir / settings.get("output_markdown", "reports/intake/new_text_documents_summary.md")
    output_json = root_dir / settings.get("output_json", "results/intake/new_text_documents_index.json")

    write_markdown(output_markdown, payload)
    write_json(output_json, payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize and index repository intake text documents.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to the YAML manifest that lists intake documents.",
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=ROOT,
        help="Repository root directory used to resolve manifest paths and outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = generate_intake(manifest_path=args.manifest.resolve(), root_dir=args.root_dir.resolve())
    try:
        manifest_display = str(args.manifest.resolve().relative_to(args.root_dir.resolve()))
    except ValueError:
        manifest_display = str(args.manifest.resolve())
    print(
        "Generated intake outputs for "
        f"{payload['documents_processed']} documents using {manifest_display}"
    )


if __name__ == "__main__":
    main()
