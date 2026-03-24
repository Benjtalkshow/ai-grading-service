import os
import re
import shutil
import json
from typing import Dict, Any, List
from git import Repo
from radon.complexity import cc_visit, cc_rank
import subprocess

# Language extensions mapping
LANGUAGE_MAP = {
    ".rs": "Rust", ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript (React)", ".jsx": "JavaScript (React)", ".sol": "Solidity",
    ".go": "Go", ".java": "Java", ".cpp": "C++", ".c": "C", ".cs": "C#",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".dart": "Dart", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".toml": "TOML", ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".md": "Markdown", ".sh": "Shell", ".sql": "SQL", ".graphql": "GraphQL",
}

# File patterns indicating test files
TEST_PATTERNS = [
    r"test[_\-]", r"[_\-]test\.", r"\.test\.", r"\.spec\.",
    r"tests/", r"__tests__/", r"test/", r"spec/",
]

# CI/CD config files
CI_CD_FILES = [
    ".github/workflows", "Jenkinsfile", ".gitlab-ci.yml", ".circleci",
    ".travis.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
]

# Dependency manifests
DEPENDENCY_FILES = {
    "Cargo.toml": "Rust", "package.json": "JavaScript/TypeScript",
    "requirements.txt": "Python", "Pipfile": "Python", "pyproject.toml": "Python",
    "go.mod": "Go", "pom.xml": "Java", "build.gradle": "Java/Kotlin",
    "Gemfile": "Ruby", "composer.json": "PHP",
}

# Soroban/Stellar-specific patterns to search for in Rust files
SOROBAN_PATTERNS = {
    "contract_annotation": r"#\[contract\]",
    "contractimpl": r"#\[contractimpl\]",
    "contracttype": r"#\[contracttype\]",
    "soroban_sdk_import": r"soroban_sdk",
    "require_auth": r"require_auth\s*\(",
    "env_usage": r"Env\b",
    "storage_instance": r"storage\(\)\s*\.\s*instance\(\)",
    "storage_persistent": r"storage\(\)\s*\.\s*persistent\(\)",
    "storage_temporary": r"storage\(\)\s*\.\s*temporary\(\)",
    "extend_ttl": r"extend_ttl\s*\(",
    "checked_add": r"checked_add\s*\(",
    "checked_sub": r"checked_sub\s*\(",
    "checked_mul": r"checked_mul\s*\(",
    "token_interface": r"token::",
    "event_publish": r"events\(\)\s*\.\s*publish\s*\(",
    "no_std": r"#!\[no_std\]",
    "panic_usage": r"\bpanic!\s*\(",
    "unwrap_usage": r"\.unwrap\(\)",
    "unsafe_block": r"\bunsafe\s*\{",
    "init_guard": r"already.?initialized|is_initialized|initialized",
}

# Security anti-patterns across languages
SECURITY_ANTIPATTERNS = {
    "hardcoded_secret": r"(?i)(api[_\-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    "eval_usage": r"\beval\s*\(",
    "exec_usage": r"\bexec\s*\(",
    "sql_injection": r"(?i)f['\"].*(?:SELECT|INSERT|UPDATE|DELETE).*\{",
    "cors_wildcard": r"(?i)Access-Control-Allow-Origin.*\*",
    "http_no_tls": r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)",
}


class RepoAnalyzer:
    """Advanced GitHub repository analyzer with multi-language and Soroban-specific analysis"""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    async def analyze_repo(self, github_url: str) -> Dict[str, Any]:
        """Clone and perform comprehensive analysis of a repository"""
        if not github_url or "github.com" not in github_url:
            return {"error": "Invalid GitHub URL"}

        repo_name = github_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(self.temp_dir, repo_name)

        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)

        try:
            print(f"   📥 Cloning {github_url}...")
            # Full clone for git history analysis (limited depth for performance)
            repo = Repo.clone_from(github_url, clone_path, depth=50)

            print(f"   📊 Analyzing code structure...")
            cloc = self._run_cloc(clone_path)
            primary_lang = self._detect_primary_language(cloc)

            print(f"   🔍 Scanning for patterns and security...")
            soroban_analysis = self._analyze_soroban_patterns(clone_path)
            security_scan = self._scan_security(clone_path)
            test_analysis = self._analyze_tests(clone_path)
            dependency_analysis = self._analyze_dependencies(clone_path)
            project_structure = self._analyze_project_structure(clone_path)
            git_analysis = self._analyze_git_history(repo)
            complexity = self._analyze_complexity(clone_path, primary_lang)
            source_samples = self._extract_key_source_code(clone_path, soroban_analysis)

            analysis = {
                "cloc": cloc,
                "primary_language": primary_lang,
                "complexity": complexity,
                "readme": self._read_readme(clone_path),
                "soroban_analysis": soroban_analysis,
                "security_scan": security_scan,
                "test_analysis": test_analysis,
                "dependency_analysis": dependency_analysis,
                "project_structure": project_structure,
                "git_history": git_analysis,
                "source_code_samples": source_samples,
            }
            print(f"   ✅ Comprehensive analysis complete.")

            return analysis
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
        finally:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)

    def _run_cloc(self, path: str) -> Dict[str, Any]:
        """Count lines of code by language with detailed breakdown"""
        stats = {
            "total_files": 0,
            "total_lines": 0,
            "code_lines": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "languages": {},
            "language_lines": {},
        }
        comment_patterns = {
            ".py": r"^\s*#",
            ".rs": r"^\s*//",
            ".js": r"^\s*//",
            ".ts": r"^\s*//",
            ".tsx": r"^\s*//",
            ".jsx": r"^\s*//",
            ".go": r"^\s*//",
            ".java": r"^\s*//",
            ".sol": r"^\s*//",
        }

        for root, dirs, files in os.walk(path):
            # Skip hidden dirs, node_modules, build artifacts
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('node_modules', 'target', 'build', 'dist', '__pycache__', '.git', 'vendor')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if not ext or ext in ('.lock', '.svg', '.png', '.jpg', '.gif', '.ico', '.woff', '.woff2', '.eot', '.ttf'):
                    continue
                stats["total_files"] += 1
                lang_name = LANGUAGE_MAP.get(ext, ext)
                stats["languages"][lang_name] = stats["languages"].get(lang_name, 0) + 1

                try:
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', errors='ignore') as f:
                        lines = f.readlines()
                    line_count = len(lines)
                    stats["total_lines"] += line_count
                    stats["language_lines"][lang_name] = stats["language_lines"].get(lang_name, 0) + line_count

                    comment_pat = comment_patterns.get(ext)
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            stats["blank_lines"] += 1
                        elif comment_pat and re.match(comment_pat, line):
                            stats["comment_lines"] += 1
                        else:
                            stats["code_lines"] += 1
                except Exception:
                    pass
        return stats

    def _detect_primary_language(self, cloc: Dict) -> str:
        """Determine the primary programming language"""
        lang_lines = cloc.get("language_lines", {})
        # Filter out non-code languages
        code_langs = {k: v for k, v in lang_lines.items()
                      if k not in ("Markdown", "JSON", "YAML", "TOML", "HTML", "CSS", "SCSS", "Shell")}
        if code_langs:
            return max(code_langs, key=code_langs.get)
        return "Unknown"

    def _analyze_soroban_patterns(self, path: str) -> Dict[str, Any]:
        """Deep analysis of Soroban/Stellar smart contract patterns"""
        result = {
            "is_soroban_project": False,
            "contracts_found": 0,
            "patterns_detected": {},
            "security_checklist": {},
            "quality_signals": [],
            "issues": [],
        }

        rust_files = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'target']
            for file in files:
                if file.endswith('.rs'):
                    rust_files.append(os.path.join(root, file))

        if not rust_files:
            # Check if Cargo.toml references soroban
            cargo_path = os.path.join(path, "Cargo.toml")
            if os.path.exists(cargo_path):
                try:
                    with open(cargo_path, 'r') as f:
                        cargo_content = f.read()
                    if 'soroban' in cargo_content.lower():
                        result["is_soroban_project"] = True
                        result["quality_signals"].append("Soroban SDK found in Cargo.toml but no Rust source files in repo")
                except Exception:
                    pass
            return result

        # Check all Cargo.toml files for soroban dependency
        for root, _, files in os.walk(path):
            for file in files:
                if file == "Cargo.toml":
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            content = f.read()
                        if 'soroban' in content.lower():
                            result["is_soroban_project"] = True
                    except Exception:
                        pass

        # Scan Rust files for Soroban patterns
        pattern_counts = {k: 0 for k in SOROBAN_PATTERNS}
        contract_files = []

        for filepath in rust_files:
            try:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()

                is_contract_file = False
                for pattern_name, pattern in SOROBAN_PATTERNS.items():
                    matches = len(re.findall(pattern, content))
                    if matches > 0:
                        pattern_counts[pattern_name] += matches
                        if pattern_name in ("contract_annotation", "contractimpl"):
                            is_contract_file = True

                if is_contract_file:
                    contract_files.append(os.path.relpath(filepath, path))
                    result["contracts_found"] += 1
            except Exception:
                pass

        result["patterns_detected"] = {k: v for k, v in pattern_counts.items() if v > 0}

        # Security checklist based on patterns found
        has_auth = pattern_counts["require_auth"] > 0
        has_checked_math = any(pattern_counts[k] > 0 for k in ["checked_add", "checked_sub", "checked_mul"])
        has_init_guard = pattern_counts["init_guard"] > 0
        has_no_std = pattern_counts["no_std"] > 0
        has_events = pattern_counts["event_publish"] > 0
        has_storage_mgmt = any(pattern_counts[k] > 0 for k in ["storage_instance", "storage_persistent", "storage_temporary"])
        has_ttl = pattern_counts["extend_ttl"] > 0
        has_panics = pattern_counts["panic_usage"] > 0
        has_unwraps = pattern_counts["unwrap_usage"] > 0
        has_unsafe = pattern_counts["unsafe_block"] > 0

        result["security_checklist"] = {
            "authorization_checks": {"present": has_auth, "count": pattern_counts["require_auth"],
                                     "critical": True, "note": "require_auth() guards privileged operations"},
            "checked_arithmetic": {"present": has_checked_math,
                                   "critical": True, "note": "Prevents integer overflow/underflow"},
            "initialization_guard": {"present": has_init_guard,
                                     "critical": True, "note": "Prevents contract reinitialization attacks"},
            "no_std_compliance": {"present": has_no_std,
                                  "critical": False, "note": "Required for Soroban contracts"},
            "event_emission": {"present": has_events,
                               "critical": False, "note": "Important for auditability and indexing"},
            "storage_management": {"present": has_storage_mgmt,
                                   "critical": False, "note": "Proper use of Instance/Persistent/Temporary storage"},
            "ttl_management": {"present": has_ttl,
                               "critical": False, "note": "extend_ttl() for storage expiry management"},
        }

        # Quality signals and issues
        if result["is_soroban_project"]:
            if has_auth:
                result["quality_signals"].append("Authorization checks (require_auth) properly implemented")
            else:
                result["issues"].append("CRITICAL: No require_auth() calls found - potential unauthorized access vulnerability")

            if has_checked_math:
                result["quality_signals"].append("Safe arithmetic (checked_add/sub/mul) used")
            elif result["contracts_found"] > 0:
                result["issues"].append("WARNING: No checked arithmetic found - potential overflow vulnerability")

            if has_init_guard:
                result["quality_signals"].append("Initialization guard pattern detected")
            elif result["contracts_found"] > 0:
                result["issues"].append("WARNING: No initialization guard detected - reinitialization attack possible")

            if has_events:
                result["quality_signals"].append("Event emission for state changes (good for indexing/auditing)")

            if has_panics:
                result["issues"].append(f"WARNING: {pattern_counts['panic_usage']} panic!() calls found - should use proper error handling")

            if has_unwraps:
                result["issues"].append(f"NOTICE: {pattern_counts['unwrap_usage']} .unwrap() calls found - may cause runtime panics")

            if has_unsafe:
                result["issues"].append(f"CRITICAL: {pattern_counts['unsafe_block']} unsafe blocks found in contract code")

            if not has_no_std and result["contracts_found"] > 0:
                result["issues"].append("WARNING: #![no_std] not detected - required for Soroban contract deployment")

        result["contract_files"] = contract_files
        return result

    def _scan_security(self, path: str) -> Dict[str, Any]:
        """Scan for security anti-patterns across all languages"""
        findings = {
            "issues": [],
            "severity_summary": {"critical": 0, "warning": 0, "notice": 0},
        }

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('node_modules', 'target', 'build', 'dist', '__pycache__', 'vendor')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in ('.rs', '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java', '.sol'):
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read()
                    rel_path = os.path.relpath(filepath, path)

                    for pattern_name, pattern in SECURITY_ANTIPATTERNS.items():
                        matches = re.findall(pattern, content)
                        if matches:
                            severity = "critical" if pattern_name in ("hardcoded_secret", "sql_injection") else "warning"
                            findings["issues"].append({
                                "type": pattern_name,
                                "file": rel_path,
                                "severity": severity,
                                "occurrences": len(matches),
                            })
                            findings["severity_summary"][severity] += 1
                except Exception:
                    pass

        # Check for .env files committed to repo
        for root, _, files in os.walk(path):
            for file in files:
                if file in ('.env', '.env.local', '.env.production'):
                    findings["issues"].append({
                        "type": "env_file_committed",
                        "file": os.path.relpath(os.path.join(root, file), path),
                        "severity": "critical",
                        "occurrences": 1,
                    })
                    findings["severity_summary"]["critical"] += 1

        return findings

    def _analyze_tests(self, path: str) -> Dict[str, Any]:
        """Analyze test coverage and testing practices"""
        result = {
            "has_tests": False,
            "test_files": [],
            "test_file_count": 0,
            "test_frameworks_detected": [],
            "test_to_code_ratio": 0.0,
            "test_lines": 0,
            "code_lines": 0,
        }

        test_frameworks = {
            "pytest": r"(?:import pytest|from pytest|@pytest\.)",
            "jest": r"(?:describe\s*\(|it\s*\(|test\s*\(|expect\s*\()",
            "mocha": r"(?:describe\s*\(|it\s*\(|chai)",
            "rust_test": r"#\[cfg\(test\)\]|#\[test\]",
            "go_test": r"func\s+Test\w+\s*\(",
            "junit": r"@Test|import org\.junit",
        }

        detected_frameworks = set()

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('node_modules', 'target', 'build', 'dist', '__pycache__', 'vendor')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in ('.rs', '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java'):
                    continue

                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, path)
                is_test = any(re.search(p, rel_path) for p in TEST_PATTERNS)

                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read()
                    line_count = content.count('\n')

                    # Also check content for test patterns (e.g. Rust inline tests)
                    for framework, pattern in test_frameworks.items():
                        if re.search(pattern, content):
                            detected_frameworks.add(framework)
                            if not is_test and framework == "rust_test":
                                is_test = True  # Rust inline test modules

                    if is_test:
                        result["test_files"].append(rel_path)
                        result["test_lines"] += line_count
                    else:
                        result["code_lines"] += line_count
                except Exception:
                    pass

        result["test_file_count"] = len(result["test_files"])
        result["has_tests"] = result["test_file_count"] > 0
        result["test_frameworks_detected"] = list(detected_frameworks)
        if result["code_lines"] > 0:
            result["test_to_code_ratio"] = round(result["test_lines"] / result["code_lines"], 3)
        # Limit file list for prompt size
        result["test_files"] = result["test_files"][:20]
        return result

    def _analyze_dependencies(self, path: str) -> Dict[str, Any]:
        """Analyze project dependencies and detect key libraries"""
        result = {
            "manifests_found": [],
            "dependency_count": 0,
            "key_dependencies": [],
            "stellar_dependencies": [],
        }

        stellar_keywords = ["soroban", "stellar", "horizon", "freighter", "passkey"]

        for root, _, files in os.walk(path):
            if any(skip in root for skip in ['.git', 'node_modules', 'target', '__pycache__']):
                continue
            for file in files:
                if file in DEPENDENCY_FILES:
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, path)
                    result["manifests_found"].append({
                        "file": rel_path,
                        "language": DEPENDENCY_FILES[file]
                    })

                    try:
                        with open(filepath, 'r', errors='ignore') as f:
                            content = f.read()

                        deps = self._extract_dependency_names(file, content)
                        result["dependency_count"] += len(deps)

                        for dep in deps:
                            dep_lower = dep.lower()
                            if any(kw in dep_lower for kw in stellar_keywords):
                                result["stellar_dependencies"].append(dep)
                            # Detect notable dependencies
                            if any(kw in dep_lower for kw in ["react", "next", "vue", "angular", "express",
                                                               "fastapi", "django", "flask", "actix", "rocket",
                                                               "tokio", "serde", "wasm"]):
                                result["key_dependencies"].append(dep)
                    except Exception:
                        pass

        result["key_dependencies"] = list(set(result["key_dependencies"]))[:30]
        result["stellar_dependencies"] = list(set(result["stellar_dependencies"]))
        return result

    def _extract_dependency_names(self, filename: str, content: str) -> List[str]:
        """Extract dependency names from a manifest file"""
        deps = []
        try:
            if filename == "package.json":
                data = json.loads(content)
                for key in ("dependencies", "devDependencies"):
                    if key in data:
                        deps.extend(data[key].keys())
            elif filename == "Cargo.toml":
                # Simple TOML dep extraction
                in_deps = False
                for line in content.split('\n'):
                    if re.match(r'\[(.*dependencies.*)\]', line):
                        in_deps = True
                        continue
                    if line.startswith('[') and in_deps:
                        in_deps = False
                        continue
                    if in_deps:
                        match = re.match(r'(\S+)\s*=', line)
                        if match:
                            deps.append(match.group(1))
            elif filename == "requirements.txt":
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps.append(re.split(r'[=<>!~]', line)[0].strip())
            elif filename in ("go.mod",):
                for line in content.split('\n'):
                    match = re.match(r'\s+(\S+)\s+v', line)
                    if match:
                        deps.append(match.group(1).split('/')[-1])
        except Exception:
            pass
        return deps

    def _analyze_project_structure(self, path: str) -> Dict[str, Any]:
        """Analyze the project's organizational structure"""
        result = {
            "has_ci_cd": False,
            "ci_cd_type": [],
            "has_documentation": False,
            "has_license": False,
            "has_contributing": False,
            "has_docker": False,
            "has_config_management": False,
            "directory_structure": [],
            "notable_files": [],
        }

        # Check for CI/CD
        for ci_path in CI_CD_FILES:
            full_path = os.path.join(path, ci_path)
            if os.path.exists(full_path):
                result["has_ci_cd"] = True
                result["ci_cd_type"].append(ci_path)

        # Check for key files
        top_files = os.listdir(path)
        for f in top_files:
            f_lower = f.lower()
            if f_lower.startswith("readme"):
                result["has_documentation"] = True
            if f_lower in ("license", "license.md", "license.txt"):
                result["has_license"] = True
            if f_lower.startswith("contributing"):
                result["has_contributing"] = True
            if f_lower in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                result["has_docker"] = True
            if f_lower in (".env.example", ".env.sample", "config.toml", "config.yaml"):
                result["has_config_management"] = True

        # Get top-level directory structure (1 level deep)
        for item in sorted(top_files):
            item_path = os.path.join(path, item)
            if item.startswith('.'):
                continue
            if os.path.isdir(item_path):
                sub_items = []
                try:
                    sub_items = [si for si in os.listdir(item_path) if not si.startswith('.')][:10]
                except Exception:
                    pass
                result["directory_structure"].append(f"{item}/ ({len(sub_items)} items)")
            else:
                result["notable_files"].append(item)

        return result

    def _analyze_git_history(self, repo: Repo) -> Dict[str, Any]:
        """Analyze git commit history for development patterns"""
        result = {
            "total_commits": 0,
            "contributors": [],
            "contributor_count": 0,
            "first_commit_date": None,
            "last_commit_date": None,
            "development_duration_days": 0,
            "commit_frequency_signals": [],
            "suspicious_patterns": [],
        }

        try:
            commits = list(repo.iter_commits('HEAD', max_count=200))
            result["total_commits"] = len(commits)

            if not commits:
                return result

            # Contributor analysis
            contributors = {}
            commit_times = []
            for commit in commits:
                author = commit.author.name
                contributors[author] = contributors.get(author, 0) + 1
                commit_times.append(commit.committed_datetime)

            result["contributors"] = [
                {"name": name, "commits": count}
                for name, count in sorted(contributors.items(), key=lambda x: -x[1])
            ]
            result["contributor_count"] = len(contributors)

            # Timeline
            if commit_times:
                first = min(commit_times)
                last = max(commit_times)
                result["first_commit_date"] = first.isoformat()
                result["last_commit_date"] = last.isoformat()
                result["development_duration_days"] = (last - first).days

            # Suspicious patterns
            if result["total_commits"] <= 2 and result["development_duration_days"] == 0:
                result["suspicious_patterns"].append(
                    "Very few commits with no development timeline - may indicate a bulk upload or template fork"
                )

            # Check for single massive initial commit
            if commits:
                initial = commits[-1]
                try:
                    initial_stats = initial.stats.total
                    if initial_stats.get("lines", 0) > 5000 and result["total_commits"] < 5:
                        result["suspicious_patterns"].append(
                            f"Initial commit has {initial_stats.get('lines', 0)} lines with very few follow-up commits"
                        )
                except Exception:
                    pass

            # Commit message quality
            msg_lengths = [len(c.message.strip()) for c in commits[:50]]
            avg_msg_len = sum(msg_lengths) / len(msg_lengths) if msg_lengths else 0
            if avg_msg_len < 10:
                result["commit_frequency_signals"].append("Very short commit messages - may indicate rushed development")
            elif avg_msg_len > 30:
                result["commit_frequency_signals"].append("Descriptive commit messages - indicates good development practices")

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_complexity(self, path: str, primary_language: str) -> List[Dict[str, Any]]:
        """Run complexity analysis (Python via radon, heuristic for others)"""
        complexities = []

        if primary_language == "Python":
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'target', '__pycache__')]
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                code = f.read()
                            avg_complexity = cc_visit(code)
                            if avg_complexity:
                                avg_cc = sum(c.complexity for c in avg_complexity) / len(avg_complexity)
                                complexities.append({
                                    "file": os.path.relpath(file_path, path),
                                    "functions": len(avg_complexity),
                                    "avg_complexity": round(avg_cc, 2),
                                    "max_complexity": max(c.complexity for c in avg_complexity),
                                    "rank": cc_rank(avg_cc),
                                })
                        except Exception:
                            pass

        # For Rust/JS/TS - heuristic complexity based on nesting and function count
        elif primary_language in ("Rust", "JavaScript", "TypeScript", "TypeScript (React)", "JavaScript (React)"):
            ext_map = {"Rust": ".rs", "JavaScript": ".js", "TypeScript": ".ts",
                       "TypeScript (React)": ".tsx", "JavaScript (React)": ".jsx"}
            target_ext = ext_map.get(primary_language, ".rs")

            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                           ('node_modules', 'target', 'build', 'dist', '__pycache__')]
                for file in files:
                    if file.endswith(target_ext):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', errors='ignore') as f:
                                content = f.read()

                            lines = content.split('\n')
                            # Heuristic: count nesting depth, function count
                            max_depth = 0
                            current_depth = 0
                            fn_count = 0
                            for line in lines:
                                current_depth += line.count('{') - line.count('}')
                                max_depth = max(max_depth, current_depth)
                                if re.search(r'(?:fn |function |const \w+ = (?:async )?\(|=> \{|pub fn )', line):
                                    fn_count += 1

                            if fn_count > 0:
                                # Simple rank based on nesting
                                rank = "A" if max_depth <= 4 else "B" if max_depth <= 6 else "C" if max_depth <= 8 else "D"
                                complexities.append({
                                    "file": os.path.relpath(file_path, path),
                                    "functions": fn_count,
                                    "max_nesting_depth": max_depth,
                                    "lines": len(lines),
                                    "rank": rank,
                                })
                        except Exception:
                            pass

        # Sort by complexity (worst first) and limit
        complexities.sort(key=lambda x: x.get("max_complexity", x.get("max_nesting_depth", 0)), reverse=True)
        return complexities[:25]

    def _extract_key_source_code(self, path: str, soroban_analysis: Dict) -> Dict[str, str]:
        """Extract key source code snippets for AI analysis (contracts, main files)"""
        samples = {}
        max_sample_size = 8000  # chars per file
        total_budget = 30000  # total chars across all samples

        # Priority 1: Soroban contract files
        contract_files = soroban_analysis.get("contract_files", [])
        for cf in contract_files[:5]:
            filepath = os.path.join(path, cf)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read()[:max_sample_size]
                    samples[cf] = content
                except Exception:
                    pass

        # Priority 2: Main entry point files
        entry_points = [
            "src/lib.rs", "src/main.rs", "lib.rs",
            "src/index.ts", "src/index.js", "src/app.ts", "src/app.js",
            "index.ts", "index.js", "app.ts", "app.js",
            "src/main.py", "main.py", "app.py",
            "src/App.tsx", "src/App.jsx",
        ]
        for ep in entry_points:
            if len(json.dumps(samples)) > total_budget:
                break
            filepath = os.path.join(path, ep)
            if os.path.exists(filepath) and ep not in samples:
                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read()[:max_sample_size]
                    samples[ep] = content
                except Exception:
                    pass

        # Priority 3: Any Rust files with soroban imports (if not already captured)
        if soroban_analysis.get("is_soroban_project") and len(samples) < 5:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'target']
                if len(json.dumps(samples)) > total_budget:
                    break
                for file in files:
                    if file.endswith('.rs'):
                        filepath = os.path.join(root, file)
                        rel = os.path.relpath(filepath, path)
                        if rel not in samples:
                            try:
                                with open(filepath, 'r', errors='ignore') as f:
                                    content = f.read()
                                if 'soroban_sdk' in content:
                                    samples[rel] = content[:max_sample_size]
                            except Exception:
                                pass

        return samples

    def _read_readme(self, path: str) -> str:
        """Find and read README file"""
        for root, _, files in os.walk(path):
            for file in files:
                if file.upper().startswith("README"):
                    try:
                        with open(os.path.join(root, file), 'r', errors='ignore') as f:
                            return f.read()[:8000]
                    except Exception:
                        pass
            break  # Only check root directory
        return ""
