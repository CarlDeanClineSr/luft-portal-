#!/usr/bin/env python3
"""
Auto-resolve git conflict markers in CSV files by keeping 'ours' version.

This script scans CSV files for git conflict markers and removes them,
keeping the content from the 'ours' side (Updated upstream / current branch).
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple


def has_conflict_markers(content: str) -> bool:
    """Check if content has git conflict markers (exact 7-character match)."""
    lines = content.split('\n')
    for line in lines:
        stripped = line.rstrip('\r')
        if len(stripped) >= 7:
            marker = stripped[:7]
            if marker in ('<<<<<<< ', '=======', '>>>>>>> '):
                # Check that the 8th character is space or end of line
                if len(stripped) == 7 or stripped[7] in (' ', '\t'):
                    return True
    return False


def clean_conflict_markers(content: str) -> Tuple[str, int]:
    """
    Remove git conflict markers from content, keeping 'ours' version.
    
    Returns:
        Tuple of (cleaned_content, num_conflicts_resolved)
    """
    lines = content.split('\n')
    cleaned_lines = []
    in_conflict = False
    conflict_section = None  # 'ours', 'theirs', or None
    conflicts_resolved = 0
    
    for line in lines:
        stripped = line.rstrip('\r')
        
        # Check for conflict markers (exact 7 characters)
        if len(stripped) >= 7:
            marker = stripped[:7]
            
            # Validate it's a real marker (8th char must be space/tab or EOL)
            is_valid_marker = (len(stripped) == 7 or stripped[7] in (' ', '\t'))
            
            if marker == '<<<<<<<' and is_valid_marker:
                in_conflict = True
                conflict_section = 'ours'
                continue
            elif marker == '=======' and is_valid_marker:
                if in_conflict:
                    conflict_section = 'theirs'
                    continue
            elif marker == '>>>>>>>' and is_valid_marker:
                if in_conflict:
                    in_conflict = False
                    conflict_section = None
                    conflicts_resolved += 1
                    continue
        
        # Keep lines that are not in 'theirs' section
        if not in_conflict or conflict_section == 'ours':
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), conflicts_resolved


def process_csv_file(filepath: Path) -> bool:
    """
    Process a single CSV file to remove conflict markers.
    
    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        
        if not has_conflict_markers(content):
            return False
        
        cleaned_content, num_conflicts = clean_conflict_markers(content)
        
        # Write cleaned content back
        filepath.write_text(cleaned_content, encoding='utf-8')
        
        print(f"✅ Resolved {num_conflicts} conflict(s) in {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: clean_csv_conflicts.py <csv_file> [csv_file...]", file=sys.stderr)
        sys.exit(1)
    
    modified_count = 0
    error_count = 0
    
    for csv_path_str in sys.argv[1:]:
        csv_path = Path(csv_path_str)
        
        if not csv_path.exists():
            print(f"⚠️ File not found: {csv_path}", file=sys.stderr)
            error_count += 1
            continue
        
        if not csv_path.is_file():
            print(f"⚠️ Not a file: {csv_path}", file=sys.stderr)
            error_count += 1
            continue
        
        try:
            if process_csv_file(csv_path):
                modified_count += 1
        except Exception as e:
            print(f"❌ Failed to process {csv_path}: {e}", file=sys.stderr)
            error_count += 1
    
    if error_count > 0:
        print(f"\n⚠️ Completed with {error_count} error(s)", file=sys.stderr)
        sys.exit(1)
    
    if modified_count > 0:
        print(f"\n✅ Cleaned {modified_count} file(s)")
    else:
        print("\n✅ No conflict markers found")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
