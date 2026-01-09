#!/usr/bin/env python3
"""
Cross-Repo Index Builder for LUFT Portal
Enumerates public repos for CarlDeanClineSr via GitHub API,
fetches data/knowledge/index.json and results/teacher/aggregate_index.json,
produces data/knowledge/org_index.json and docs/VAULT_NAVIGATOR.md
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error

# Configuration
MAX_FILES_PER_REPO = int(os.getenv("MAX_FILES_PER_REPO", "100"))

GITHUB_USER = "CarlDeanClineSr"
GITHUB_API_BASE = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"


def fetch_json_url(url: str, timeout: int = 10) -> Optional[Dict]:
    """Fetch JSON from a URL with error handling."""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'LUFT-Portal-Indexer/1.0')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def get_public_repos(username: str) -> List[Dict]:
    """Fetch all public repositories for a GitHub user."""
    repos = []
    page = 1
    per_page = 100
    
    print(f"🔍 Fetching public repos for {username}...")
    
    while True:
        url = f"{GITHUB_API_BASE}/users/{username}/repos?page={page}&per_page={per_page}&type=public"
        data = fetch_json_url(url)
        
        if not data or not isinstance(data, list):
            break
            
        repos.extend(data)
        print(f"  📦 Found {len(data)} repos on page {page}")
        
        if len(data) < per_page:
            break
            
        page += 1
    
    print(f"✅ Total public repos: {len(repos)}")
    return repos


def fetch_repo_knowledge_index(owner: str, repo: str, branch: str = "main") -> Optional[Dict]:
    """Fetch data/knowledge/index.json from a repo."""
    # Try main branch first, then master
    for br in [branch, "master", "main"]:
        url = f"{RAW_BASE}/{owner}/{repo}/{br}/data/knowledge/index.json"
        result = fetch_json_url(url)
        if result:
            return result
    return None


def fetch_repo_teacher_index(owner: str, repo: str, branch: str = "main") -> Optional[Dict]:
    """Fetch results/teacher/aggregate_index.json from a repo."""
    # Try main branch first, then master
    for br in [branch, "master", "main"]:
        url = f"{RAW_BASE}/{owner}/{repo}/{br}/results/teacher/aggregate_index.json"
        result = fetch_json_url(url)
        if result:
            return result
    return None


def compute_teacher_summary(teacher_data: Dict) -> Dict[str, Any]:
    """Compute summary statistics from teacher aggregate index."""
    if not teacher_data or not isinstance(teacher_data, dict):
        return {}
    
    items = teacher_data.get("items", [])
    if not isinstance(items, list):
        return {}
    
    # Count analyzed
    analyzed = sum(1 for item in items if item.get("status") == "analyzed")
    
    # Compute signature stats
    signatures = ["chi_boundary", "fractal_regulator", "binary_harmonics", 
                  "electroweak_bridge", "whistler_gaps"]
    sig_stats = {}
    
    for sig in signatures:
        pass_count = 0
        total_count = 0
        for item in items:
            if sig in item and isinstance(item[sig], dict):
                total_count += 1
                if item[sig].get("pass"):
                    pass_count += 1
        sig_stats[sig] = {"pass": pass_count, "total": total_count}
    
    return {
        "total_datasets": teacher_data.get("count", len(items)),
        "analyzed": analyzed,
        "signatures": sig_stats
    }


def build_org_index(username: str) -> Dict:
    """Build the cross-repo organization index."""
    repos = get_public_repos(username)
    
    org_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "github_user": username,
        "total_repos": len(repos),
        "repos_with_knowledge": 0,
        "repos_with_teacher": 0,
        "total_files_indexed": 0,
        "repositories": []
    }
    
    print(f"\n📚 Indexing repositories...\n")
    
    for repo_info in repos:
        repo_name = repo_info["name"]
        default_branch = repo_info.get("default_branch", "main")
        
        print(f"🔎 {repo_name} ({default_branch})...")
        
        repo_entry = {
            "name": repo_name,
            "full_name": repo_info["full_name"],
            "description": repo_info.get("description", ""),
            "url": repo_info["html_url"],
            "default_branch": default_branch,
            "updated_at": repo_info.get("updated_at", ""),
            "knowledge_index": None,
            "teacher_summary": None,
            "file_count": 0
        }
        
        # Try to fetch knowledge index
        knowledge = fetch_repo_knowledge_index(username, repo_name, default_branch)
        if knowledge:
            org_data["repos_with_knowledge"] += 1
            files = knowledge.get("files", [])
            file_count = len(files) if isinstance(files, list) else knowledge.get("total_files", 0)
            org_data["total_files_indexed"] += file_count
            repo_entry["file_count"] = file_count
            repo_entry["knowledge_index"] = {
                "total_files": file_count,
                "generated_at": knowledge.get("generated_at", ""),
                "files": files[:MAX_FILES_PER_REPO] if isinstance(files, list) else []
            }
            print(f"  ✓ Knowledge index: {file_count} files")
        
        # Try to fetch teacher index
        teacher = fetch_repo_teacher_index(username, repo_name, default_branch)
        if teacher:
            org_data["repos_with_teacher"] += 1
            summary = compute_teacher_summary(teacher)
            repo_entry["teacher_summary"] = summary
            print(f"  ✓ Teacher index: {summary.get('total_datasets', 0)} datasets, {summary.get('analyzed', 0)} analyzed")
        
        org_data["repositories"].append(repo_entry)
    
    print(f"\n✅ Organization index built:")
    print(f"   • {org_data['repos_with_knowledge']} repos with knowledge indices")
    print(f"   • {org_data['repos_with_teacher']} repos with teacher indices")
    print(f"   • {org_data['total_files_indexed']} total files indexed")
    
    return org_data


def generate_vault_navigator_md(org_data: Dict) -> str:
    """Generate VAULT_NAVIGATOR.md markdown document."""
    lines = [
        "# LUFT Vault Navigator",
        "",
        f"**Generated:** {org_data['generated_at']}",
        f"**GitHub User:** {org_data['github_user']}",
        "",
        "## Summary",
        "",
        f"- **Total Repositories:** {org_data['total_repos']}",
        f"- **Repositories with Knowledge Index:** {org_data['repos_with_knowledge']}",
        f"- **Repositories with Teacher Analysis:** {org_data['repos_with_teacher']}",
        f"- **Total Files Indexed:** {org_data['total_files_indexed']}",
        "",
        "## Repositories",
        ""
    ]
    
    for repo in org_data["repositories"]:
        lines.append(f"### [{repo['name']}]({repo['url']})")
        lines.append("")
        
        if repo.get("description"):
            lines.append(f"**Description:** {repo['description']}")
            lines.append("")
        
        lines.append(f"**Branch:** {repo['default_branch']}")
        lines.append(f"**Last Updated:** {repo['updated_at']}")
        lines.append("")
        
        # Knowledge index info
        if repo.get("knowledge_index"):
            ki = repo["knowledge_index"]
            lines.append(f"**📚 Knowledge Index:** {ki['total_files']} files indexed")
            lines.append("")
            
            if ki.get("files"):
                lines.append("**Sample Files:**")
                lines.append("")
                for f in ki["files"][:10]:  # Show first 10
                    path = f.get("path", "unknown")
                    title = f.get("title", "")[:80]
                    kind = f.get("kind", "unknown")
                    lines.append(f"- `{path}` — *{kind}* — {title}")
                lines.append("")
        
        # Teacher summary info
        if repo.get("teacher_summary"):
            ts = repo["teacher_summary"]
            lines.append(f"**🎓 Teach-The-Engine:** {ts.get('analyzed', 0)}/{ts.get('total_datasets', 0)} datasets analyzed")
            lines.append("")
            
            if ts.get("signatures"):
                lines.append("**Signature Pass Rates:**")
                lines.append("")
                for sig_name, stats in ts["signatures"].items():
                    total = stats["total"]
                    passed = stats["pass"]
                    pct = round((passed / total * 100)) if total > 0 else 0
                    lines.append(f"- {sig_name}: {passed}/{total} ({pct}%)")
                lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 60)
    print("LUFT Cross-Repo Index Builder")
    print("=" * 60)
    print()
    
    # Build the organization index
    org_data = build_org_index(GITHUB_USER)
    
    # Ensure output directories exist
    os.makedirs("data/knowledge", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    # Write org_index.json
    org_index_path = "data/knowledge/org_index.json"
    print(f"\n💾 Writing {org_index_path}...")
    with open(org_index_path, "w", encoding="utf-8") as f:
        json.dump(org_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {org_index_path}")
    
    # Write VAULT_NAVIGATOR.md
    vault_md = generate_vault_navigator_md(org_data)
    vault_md_path = "docs/VAULT_NAVIGATOR.md"
    print(f"\n💾 Writing {vault_md_path}...")
    with open(vault_md_path, "w", encoding="utf-8") as f:
        f.write(vault_md)
    print(f"✅ Wrote {vault_md_path}")
    
    print("\n" + "=" * 60)
    print("✅ Cross-repo index build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
