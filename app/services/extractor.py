import os
import shutil
import tempfile
from typing import Dict, Any, List
from git import Repo
from radon.complexity import cc_visit, cc_rank
from radon.metrics import h_visit
import subprocess

class RepoAnalyzer:
    """Clones and analyzes GitHub repositories"""
    
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    async def analyze_repo(self, github_url: str) -> Dict[str, Any]:
        """Clone and analyze a repository"""
        if not github_url or "github.com" not in github_url:
            return {"error": "Invalid GitHub URL"}

        repo_name = github_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(self.temp_dir, repo_name)

        # Cleanup if exists
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)

        try:
            # Clone repo
            print(f"   📥 Cloning {github_url}...")
            Repo.clone_from(github_url, clone_path, depth=1)
            
            # Run analysis
            print(f"   📊 Analyzing code structure...")
            analysis = {
                "cloc": self._run_cloc(clone_path),
                "complexity": self._analyze_complexity(clone_path),
                "readme": self._read_readme(clone_path)
            }
            print(f"   ✅ Analysis complete.")
            
            return analysis
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
        finally:
            # Cleanup
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)

    def _run_cloc(self, path: str) -> Dict[str, Any]:
        """Simple line count (fallback if cloc not installed)"""
        stats = {"total_files": 0, "total_lines": 0, "languages": {}}
        for root, _, files in os.walk(path):
            if ".git" in root:
                continue
            for file in files:
                ext = os.path.splitext(file)[1]
                if not ext: continue
                stats["total_files"] += 1
                stats["languages"][ext] = stats["languages"].get(ext, 0) + 1
                try:
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        stats["total_lines"] += len(f.readlines())
                except:
                    pass
        return stats

    def _analyze_complexity(self, path: str) -> List[Dict[str, Any]]:
        """Run radon complexity analysis on Python files"""
        complexities = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            code = f.read()
                            avg_complexity = cc_visit(code)
                            if avg_complexity:
                                complexities.append({
                                    "file": os.path.relpath(file_path, path),
                                    "complexity": [c.complexity for c in avg_complexity],
                                    "rank": cc_rank(sum(c.complexity for c in avg_complexity) / len(avg_complexity)) if avg_complexity else "A"
                                })
                    except:
                        pass
        return complexities[:20]  # Limit to top 20 files

    def _read_readme(self, path: str) -> str:
        """Find and read README file"""
        for root, _, files in os.walk(path):
            for file in files:
                if file.upper().startswith("README"):
                    try:
                        with open(os.path.join(root, file), 'r', errors='ignore') as f:
                            return f.read()[:5000] # Limit to 5k chars
                    except:
                        pass
        return ""
