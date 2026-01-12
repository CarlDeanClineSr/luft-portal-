#!/usr/bin/env python3
"""Regenerate LUFT dashboards with the latest heartbeat + meta data."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Dict, List, Optional

import logging
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
HEARTBEAT_PATTERN = re.compile(r"cme_heartbeat_log_\d{4}_\d{2}\.csv")
CONFLICT_MARKER_LENGTH = 7
CONFLICT_MARKER_PATTERN = re.compile(
    rf"^(<{{{CONFLICT_MARKER_LENGTH}}}[^\r\n]*|={{{CONFLICT_MARKER_LENGTH}}}|>{{{CONFLICT_MARKER_LENGTH}}}[^\r\n]*)$",
    re.MULTILINE,
)

# Pages that should receive the live summary block
HTML_PAGES: Dict[str, Dict[str, bool]] = {
    "index.html": {"include_meta": True},
    "instrument-panel.html": {"include_meta": False},
    "meta-intelligence.html": {"include_meta": True},
    "temporal_correlation_dashboard.html": {"include_meta": True},
}

# JS assets that embed the heartbeat CSV path
JS_ASSETS: List[str] = ["js/dashboard-live.js", "js/instrument-panel.js"]


def validate_csv_no_conflicts(filepath: Path) -> None:
    """Ensure CSV file does not contain git merge conflict markers."""
    content = filepath.read_text(encoding="utf-8")
    if CONFLICT_MARKER_PATTERN.search(content):
        raise ValueError(f"Git conflict markers found in {filepath}. Resolve before parsing.")


def find_latest_heartbeat() -> Optional[Path]:
    candidates = sorted(ROOT.joinpath("data").glob("cme_heartbeat_log_*.csv"))
    if not candidates:
        return None
    # Prefer newest by mtime, then by name
    return max(candidates, key=lambda p: (p.stat().st_mtime, p.name))


def compute_today_metrics(csv_path: Path) -> Dict[str, Optional[float]]:
    validate_csv_no_conflicts(csv_path)

    bad_lines: List[List[str]] = []

    def _collect_bad_lines(bad_line):
        bad_lines.append(bad_line)
        return None

    df = pd.read_csv(csv_path, on_bad_lines=_collect_bad_lines, engine="python")
    if "timestamp_utc" not in df.columns:
        raise ValueError("Expected timestamp_utc column in heartbeat log")

    parsed_rows = len(df)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp_utc"])
    timestamp_dropped = parsed_rows - len(df)
    total_dropped = len(bad_lines) + timestamp_dropped
    if total_dropped:
        logging.warning(
            "Dropped %s malformed rows while parsing %s (parser rejects: %s, invalid timestamps: %s)",
            total_dropped,
            csv_path.name,
            len(bad_lines),
            timestamp_dropped,
        )
    if df.empty:
        raise ValueError(f"No valid rows found in {csv_path}")

    df["date"] = df["timestamp_utc"].dt.date

    today = datetime.now(timezone.utc).date()
    today_df = df[df["date"] == today]
    latest = df.iloc[-1]

    def safe_float(series_name: str) -> Optional[float]:
        val = latest.get(series_name)
        try:
            if pd.notna(val):
                return float(val)
        except Exception:
            return None
        return None

    return {
        "file_name": csv_path.name,
        "last_timestamp": latest["timestamp_utc"].strftime("%Y-%m-%d %H:%M:%S UTC"),
        "last_chi": safe_float("chi_amplitude"),
        "last_status": str(latest.get("chi_status", "") or "").strip(),
        "last_bz": safe_float("bz_nT"),
        "last_speed": safe_float("speed_km_s"),
        "last_density": safe_float("density_p_cm3"),
        "today_count": int(today_df.shape[0]),
        "today_boundary_hits": int(today_df["chi_at_boundary"].sum()) if "chi_at_boundary" in today_df else 0,
        "today_violations": int(today_df["chi_violation"].sum()) if "chi_violation" in today_df else 0,
        "today": today.isoformat(),
    }


def load_meta_summary() -> Optional[str]:
    summary_path = ROOT / "reports" / "meta_intelligence" / "LATEST_SUMMARY.md"
    if not summary_path.exists():
        return None
    lines = summary_path.read_text(encoding="utf-8").strip().splitlines()
    # Keep the first few non-empty lines for brevity
    cleaned = [ln.strip() for ln in lines if ln.strip()][:10]
    return "\n".join(cleaned[:8]) if cleaned else None


def render_summary_block(metrics: Dict[str, Optional[float]], meta_snippet: Optional[str], include_meta: bool) -> str:
    def fmt(val: Optional[float], digits: int = 4, suffix: str = "") -> str:
        if val is None:
            return "--"
        return f"{val:.{digits}f}{suffix}"

    meta_html = ""
    if include_meta and meta_snippet:
        meta_html = f"""
        <div style="margin-top:0.6rem;padding:0.75rem;border:1px solid #334155;border-radius:10px;background:#0b1220;">
            <div style="color:#a855f7;font-weight:700;margin-bottom:0.35rem;">Meta-Intelligence Latest</div>
            <pre style="margin:0;color:#e2e8f0;font-family:'JetBrains Mono', monospace;white-space:pre-wrap;">{meta_snippet}</pre>
        </div>
        """

    return f"""
<!-- AUTO-GENERATED DASHBOARD SUMMARY START -->
<section class="live-summary" style="margin:1rem auto;padding:1rem 1.25rem;border:1px solid #334155;border-radius:14px;background:linear-gradient(135deg,#0b1220 0%,#0a0f1c 100%);max-width:1400px;">
    <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.75rem;">
        <div>
            <div style="color:#94a3b8;font-size:0.9rem;">Refreshed {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</div>
            <div style="color:#38bdf8;font-weight:800;font-size:1.2rem;">Today's χ boundary snapshot</div>
            <div style="color:#cbd5e1;font-size:0.95rem;">Source: {metrics['file_name']} · Entries today: {metrics['today_count']}</div>
        </div>
        <div style="text-align:right;color:#fbbf24;font-weight:800;">Latest at {metrics['last_timestamp']}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.75rem;margin-top:0.75rem;">
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:0.75rem;">
            <div style="color:#94a3b8;font-size:0.85rem;">χ amplitude</div>
            <div style="color:#4ade80;font-weight:800;font-size:1.4rem;">{fmt(metrics['last_chi'])}</div>
            <div style="color:#cbd5e1;font-size:0.9rem;">Status: {metrics['last_status'] or '—'}</div>
        </div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:0.75rem;">
            <div style="color:#94a3b8;font-size:0.85rem;">Boundary hits (today)</div>
            <div style="color:#fbbf24;font-weight:800;font-size:1.4rem;">{metrics['today_boundary_hits']}</div>
            <div style="color:#cbd5e1;font-size:0.9rem;">Violations: {metrics['today_violations']}</div>
        </div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:0.75rem;">
            <div style="color:#94a3b8;font-size:0.85rem;">Solar wind speed</div>
            <div style="color:#38bdf8;font-weight:800;font-size:1.4rem;">{fmt(metrics['last_speed'], 0, ' km/s')}</div>
            <div style="color:#cbd5e1;font-size:0.9rem;">Density: {fmt(metrics['last_density'], 2, ' p/cm³')}</div>
        </div>
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:0.75rem;">
            <div style="color:#94a3b8;font-size:0.85rem;">Bz magnetic field</div>
            <div style="color:#a855f7;font-weight:800;font-size:1.4rem;">{fmt(metrics['last_bz'], 2, ' nT')}</div>
            <div style="color:#cbd5e1;font-size:0.9rem;">Date: {metrics['today']}</div>
        </div>
    </div>
    {meta_html}
</section>
<!-- AUTO-GENERATED DASHBOARD SUMMARY END -->
""".strip()


def inject_summary(html_path: Path, block: str) -> bool:
    content = html_path.read_text(encoding="utf-8")
    start = "<!-- AUTO-GENERATED DASHBOARD SUMMARY START -->"
    end = "<!-- AUTO-GENERATED DASHBOARD SUMMARY END -->"
    pattern = re.compile(f"{start}.*?{end}", re.DOTALL)

    if pattern.search(content):
        new_content = pattern.sub(block, content)
    else:
        # Insert after opening <body> tag for visibility
        body_idx = content.lower().find("<body")
        if body_idx != -1:
            close_idx = content.find(">", body_idx)
            if close_idx != -1:
                insertion_point = close_idx + 1
                new_content = content[:insertion_point] + "\n" + block + "\n" + content[insertion_point:]
            else:
                new_content = block + "\n" + content
        else:
            new_content = block + "\n" + content

    if new_content != content:
        html_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def refresh_heartbeat_references(paths: List[str], latest_name: str) -> List[Path]:
    updated: List[Path] = []
    for rel in paths:
        target = ROOT / rel
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        new_text = HEARTBEAT_PATTERN.sub(latest_name, text)
        if new_text != text:
            target.write_text(new_text, encoding="utf-8")
            updated.append(target)
    return updated


def main() -> None:
    latest = find_latest_heartbeat()
    if not latest:
        print("No heartbeat logs found; skipping dashboard regeneration.")
        return

    metrics = compute_today_metrics(latest)
    meta_snippet = load_meta_summary()

    updated_files: List[Path] = []

    summary_cache: Dict[bool, str] = {}
    for page, cfg in HTML_PAGES.items():
        include_meta = cfg.get("include_meta", False)
        if include_meta not in summary_cache:
            summary_cache[include_meta] = render_summary_block(metrics, meta_snippet, include_meta)
        block = summary_cache[include_meta]

        html_path = ROOT / page
        if html_path.exists() and inject_summary(html_path, block):
            updated_files.append(html_path)

    updated_files.extend(refresh_heartbeat_references(list(HTML_PAGES.keys()) + JS_ASSETS, metrics["file_name"]))

    if updated_files:
        print("Updated files:")
        for path in updated_files:
            print(f"- {path.relative_to(ROOT)}")
    else:
        print("No dashboard updates were necessary.")


if __name__ == "__main__":
    main()
