#!/usr/bin/env python3
"""
Capsule Index Job - Manifest Master Index Generator
Scans capsule directories for manifest YAML/JSON files, validates and merges them,
applies deduplication and versioning logic, and emits manifest_master_index.yaml.

Requirements:
- Scan capsules/ directory for .yaml, .yml, .json manifest files
- Parse and validate each manifest file
- Merge all manifests with deduplication by capsule ID
- Apply versioning logic (keep latest version)
- Generate docs/manifest_master_index.yaml

Usage:
    python scripts/capsule_index_job.py
"""

import os
import sys
import json
import yaml
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
CAPSULES_DIR = "capsules"
OUTPUT_FILE = "docs/manifest_master_index.yaml"
SUPPORTED_EXTENSIONS = [".yaml", ".yml", ".json"]

# Status values for validation
VALID_STATUSES = ["active", "draft", "archived", "deprecated", "experimental", "adopted", "template", "final"]


class CapsuleManifest:
    """Represents a single capsule manifest"""
    
    def __init__(self, filepath: str, data: Dict[str, Any]):
        self.filepath = filepath
        self.data = data
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.status = data.get("status", "draft")
        self.version = data.get("version", "1.0.0")
        self.date = data.get("date", "")
        self.author = data.get("author", "")
        self.tags = data.get("tags", [])
        self.description = data.get("description", "")
        self.errors = []
        
    def validate(self) -> bool:
        """Validate the manifest structure"""
        valid = True
        
        if not self.id:
            self.errors.append("Missing required field: id")
            valid = False
        
        if not self.title:
            self.errors.append("Missing required field: title")
            valid = False
            
        if self.status and self.status not in VALID_STATUSES:
            self.errors.append(f"Invalid status '{self.status}'. Must be one of: {', '.join(VALID_STATUSES)}")
            valid = False
            
        # Validate version format (semantic versioning)
        if self.version:
            # Convert to string if it's not already
            version_str = str(self.version)
            version_pattern = r'^\d+\.\d+\.\d+$'
            if not re.match(version_pattern, version_str):
                # Try to fix common issues (e.g., "1.0" -> "1.0.0")
                if re.match(r'^\d+\.\d+$', version_str):
                    self.version = version_str + ".0"
                elif re.match(r'^\d+$', version_str):
                    self.version = version_str + ".0.0"
                else:
                    self.errors.append(f"Invalid version format '{self.version}'. Expected semantic versioning (e.g., 1.0.0)")
                    valid = False
        
        return valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for output"""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "version": self.version,
            "date": self.date,
            "author": self.author,
            "tags": self.tags,
            "description": self.description,
            "filepath": self.filepath,
        }


def find_manifest_and_markdown_files(base_dir: str) -> tuple:
    """
    Recursively find all manifest and markdown files in a single pass.
    Returns tuple: (manifest_files, markdown_files)
    
    This combines the functionality of find_manifest_files and scan_markdown_files
    to avoid walking the directory tree twice, improving performance.
    """
    manifest_files = []
    markdown_files = []
    
    if not os.path.exists(base_dir):
        print(f"WARNING: Directory not found: {base_dir}")
        return manifest_files, markdown_files
    
    # Single pass through directory tree
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            filepath = os.path.join(root, file)
            
            # Check for explicit manifest files
            file_lower = file.lower()
            is_manifest = (
                file_lower.startswith("manifest.") or
                ".manifest." in file_lower or
                file_lower == "manifest.yaml" or
                file_lower == "manifest.yml" or
                file_lower == "manifest.json"
            )
            
            if is_manifest:
                ext = os.path.splitext(file)[1]
                if ext in SUPPORTED_EXTENSIONS:
                    manifest_files.append(filepath)
            
            # Also collect markdown files for frontmatter parsing
            elif file.endswith('.md'):
                markdown_files.append(filepath)
    
    return manifest_files, markdown_files


def parse_manifest_file(filepath: str) -> Optional[CapsuleManifest]:
    """Parse a manifest file (YAML or JSON)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Determine format by extension
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif ext == ".json":
            data = json.loads(content)
        else:
            print(f"WARNING: Unsupported file format: {filepath}")
            return None
        
        if not isinstance(data, dict):
            print(f"WARNING: Invalid manifest format (not a dict): {filepath}")
            return None
        
        # Create relative path from repo root
        rel_path = os.path.relpath(filepath)
        manifest = CapsuleManifest(rel_path, data)
        
        return manifest
        
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML file {filepath}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to read file {filepath}: {e}")
        return None


def parse_markdown_frontmatter(filepath: str) -> Optional[CapsuleManifest]:
    """Extract YAML frontmatter from markdown files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for YAML frontmatter (--- at start and end)
        if not content.startswith('---'):
            return None
        
        # Extract frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        frontmatter = parts[1].strip()
        data = yaml.safe_load(frontmatter)
        
        if not isinstance(data, dict):
            return None
        
        # Create relative path from repo root
        rel_path = os.path.relpath(filepath)
        manifest = CapsuleManifest(rel_path, data)
        
        return manifest
        
    except Exception as e:
        # Silently skip files that don't have valid frontmatter
        return None


def scan_markdown_files_from_list(markdown_files: List[str]) -> List[CapsuleManifest]:
    """
    Scan markdown files for YAML frontmatter manifests.
    Takes a pre-filtered list of markdown file paths.
    """
    manifests = []
    
    for filepath in markdown_files:
        manifest = parse_markdown_frontmatter(filepath)
        if manifest:
            manifests.append(manifest)
    
    return manifests


def deduplicate_manifests(manifests: List[CapsuleManifest]) -> List[CapsuleManifest]:
    """Deduplicate manifests by ID, keeping the latest version"""
    manifest_dict: Dict[str, CapsuleManifest] = {}
    
    for manifest in manifests:
        if not manifest.id:
            continue
        
        if manifest.id not in manifest_dict:
            manifest_dict[manifest.id] = manifest
        else:
            # Compare versions (keep higher version)
            existing = manifest_dict[manifest.id]
            
            # Parse versions for comparison
            try:
                existing_ver = tuple(map(int, existing.version.split('.')))
                new_ver = tuple(map(int, manifest.version.split('.')))
                
                if new_ver > existing_ver:
                    manifest_dict[manifest.id] = manifest
                    print(f"  Keeping newer version {manifest.version} of {manifest.id} (replaced {existing.version})")
            except (ValueError, AttributeError) as e:
                # If version parsing fails, keep the first one found
                print(f"  WARNING: Could not compare versions for {manifest.id}: {e}")
                pass
    
    return list(manifest_dict.values())


def generate_master_index(manifests: List[CapsuleManifest]) -> Dict[str, Any]:
    """Generate the master index structure"""
    
    # Sort manifests by status and then by date (newest first)
    def sort_key(m):
        status_priority = VALID_STATUSES.index(m.status) if m.status in VALID_STATUSES else 999
        # Parse date for proper sorting, fall back to old string comparison
        date_val = m.date or "0000-00-00"
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            date_sort = date_obj.timestamp()
        except (ValueError, AttributeError):
            # Fall back to string comparison for invalid dates
            date_sort = 0
        return (status_priority, -date_sort, m.id)
    
    sorted_manifests = sorted(manifests, key=sort_key)
    
    # Build index structure
    index = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "generator": "capsule_index_job.py",
            "total_capsules": len(sorted_manifests),
            "version": "1.0.0"
        },
        "statistics": {
            "by_status": {},
            "by_author": {},
            "total_tags": 0
        },
        "capsules": []
    }
    
    # Calculate statistics
    all_tags = set()
    for manifest in sorted_manifests:
        # Status counts
        status = manifest.status or "unknown"
        index["statistics"]["by_status"][status] = \
            index["statistics"]["by_status"].get(status, 0) + 1
        
        # Author counts
        author = manifest.author or "unknown"
        index["statistics"]["by_author"][author] = \
            index["statistics"]["by_author"].get(author, 0) + 1
        
        # Collect tags
        all_tags.update(manifest.tags)
        
        # Add to capsules list
        index["capsules"].append(manifest.to_dict())
    
    index["statistics"]["total_tags"] = len(all_tags)
    
    return index


def main():
    """Main execution function"""
    print("=" * 70)
    print("LUFT Portal — Capsule Index Job")
    print("=" * 70)
    print()
    
    # Find all manifest and markdown files in a single directory traversal (performance optimization)
    print(f"Scanning {CAPSULES_DIR}/ for manifest and markdown files...")
    manifest_files, markdown_files = find_manifest_and_markdown_files(CAPSULES_DIR)
    print(f"  Found {len(manifest_files)} explicit manifest files")
    print(f"  Found {len(markdown_files)} markdown files to check for frontmatter")
    
    # Parse manifest files
    manifests = []
    for filepath in manifest_files:
        manifest = parse_manifest_file(filepath)
        if manifest:
            manifests.append(manifest)
    
    # Parse markdown files for frontmatter
    md_manifests = scan_markdown_files_from_list(markdown_files)
    print(f"  Found {len(md_manifests)} markdown files with valid frontmatter")
    
    manifests.extend(md_manifests)
    
    print(f"\nTotal manifests found: {len(manifests)}")
    
    if not manifests:
        print("WARNING: No manifests found. Generating empty index.")
    
    # Validate manifests
    print("\nValidating manifests...")
    valid_count = 0
    invalid_count = 0
    
    for manifest in manifests:
        if manifest.validate():
            valid_count += 1
        else:
            invalid_count += 1
            print(f"  INVALID: {manifest.filepath}")
            for error in manifest.errors:
                print(f"    - {error}")
    
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    
    # Deduplicate manifests
    print("\nDeduplicating by capsule ID...")
    unique_manifests = deduplicate_manifests(manifests)
    print(f"  Unique capsules: {len(unique_manifests)}")
    
    # Generate master index
    print("\nGenerating master index...")
    master_index = generate_master_index(unique_manifests)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write output file
    print(f"\nWriting to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(master_index, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✅ Successfully generated manifest master index")
    print(f"   Total capsules: {master_index['metadata']['total_capsules']}")
    print(f"   Output file: {OUTPUT_FILE}")
    
    # Summary
    print("\nStatus Summary:")
    for status, count in sorted(master_index["statistics"]["by_status"].items()):
        print(f"  {status}: {count}")
    
    print("\n" + "=" * 70)
    print("Index job complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
