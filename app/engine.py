from anthropic import Anthropic
import asyncio
import json
import os
import re
import tempfile
from typing import Optional
from dotenv import load_dotenv

from .models import HackathonGradingResult, SubmissionInput, CodeQualityMetrics
from .prompts import build_grading_prompt
from .services.extractor import RepoAnalyzer
from .services.file_reader import FileExtractor
from .services.stellar_verifier import StellarVerifier
import httpx

load_dotenv()


class HackathonGradingEngine:
    """Advanced AI-powered hackathon submission grading with multi-source evidence analysis"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-6"
        self.repo_analyzer = RepoAnalyzer()
        self.file_extractor = FileExtractor()
        self.stellar_verifier = StellarVerifier()

    async def grade_submission(
        self,
        submission: SubmissionInput
    ) -> HackathonGradingResult:
        """
        Grade a hackathon submission with comprehensive evidence gathering and AI analysis.

        Pipeline:
        1. Gather all evidence in parallel (repo analysis, file extraction, on-chain verification)
        2. Format evidence into structured sections
        3. Send to Claude with calibrated scoring prompt
        4. Parse, validate, and enrich result with computed metrics
        """

        print(f"\n🏁 Starting grading for: {submission.project_name} by {submission.team_name}")

        # --- Phase 1: Parallel Evidence Gathering ---
        print(f"📡 Phase 1: Gathering evidence...")

        repo_task = self._analyze_repo(submission)
        file_task = self._extract_files(submission)
        stellar_task = self._verify_stellar(submission)

        repo_result, file_result, stellar_result = await asyncio.gather(
            repo_task, file_task, stellar_task,
            return_exceptions=True
        )

        # Handle exceptions from parallel tasks
        if isinstance(repo_result, Exception):
            print(f"   ⚠️ Repo analysis failed: {repo_result}")
            repo_result = {}
        if isinstance(file_result, Exception):
            print(f"   ⚠️ File extraction failed: {file_result}")
            file_result = ""
        if isinstance(stellar_result, Exception):
            print(f"   ⚠️ Stellar verification failed: {stellar_result}")
            stellar_result = {}

        # --- Phase 2: Format Evidence ---
        print(f"📋 Phase 2: Formatting evidence...")

        repo_evidence, soroban_evidence, source_code, code_quality_summary, code_metrics = self._format_repo_evidence(
            repo_result, submission
        )
        extracted_content = file_result if file_result else "No additional files extracted."
        stellar_evidence, contract_events = self._format_stellar_evidence(stellar_result)

        # Calculate evidence completeness
        evidence_completeness = self._calculate_evidence_completeness(
            submission, repo_result, file_result, stellar_result
        )

        # --- Phase 3: AI Grading ---
        print(f"🤖 Phase 3: AI-powered grading (model: {self.model})...")

        prompt = build_grading_prompt(
            submission=submission,
            repo_analysis=repo_evidence,
            extracted_content=extracted_content,
            stellar_evidence=stellar_evidence,
            soroban_analysis=soroban_evidence,
            source_code_samples=source_code,
            contract_events=contract_events,
            code_quality_summary=code_quality_summary,
        )

        result = await self._call_claude_with_retry(prompt)

        # --- Phase 4: Enrich & Validate ---
        print(f"✅ Phase 4: Validating and enriching result...")

        # Inject computed metrics
        if code_metrics:
            result.code_quality_metrics = code_metrics
        result.evidence_completeness = evidence_completeness

        # Verify weighted score calculation
        computed_score = self.calculate_weighted_score({
            'innovation': result.innovation.score,
            'technical_execution': result.technical_execution.score,
            'stellar_integration': result.stellar_integration.score,
            'ux_design': result.ux_design.score,
            'completeness': result.completeness.score,
        })

        # If AI's overall_score diverges significantly from weighted calculation, use computed
        if abs(result.overall_score - computed_score) > 0.5:
            print(f"   ⚠️ Score correction: AI gave {result.overall_score}, computed weighted = {computed_score}")
            result.overall_score = computed_score

        print(f"🎯 Grading complete: {result.overall_score}/10 ({result.recommendation})")
        return result

    async def _analyze_repo(self, submission: SubmissionInput) -> dict:
        """Analyze GitHub repository"""
        if not submission.github_url:
            return {}

        analysis = await self.repo_analyzer.analyze_repo(submission.github_url)
        if "error" in analysis:
            print(f"   ⚠️ Repo analysis error: {analysis['error']}")
            return {}

        # Update readme if repo version is better
        repo_readme = analysis.get('readme', '')
        if repo_readme and len(repo_readme) > len(submission.readme_content or ""):
            submission.readme_content = repo_readme

        return analysis

    async def _extract_files(self, submission: SubmissionInput) -> str:
        """Extract content from submitted files"""
        if not submission.file_urls:
            return ""

        extracted_texts = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for url in submission.file_urls:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        suffix = os.path.splitext(url.split('?')[0])[1] or '.txt'
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(resp.content)
                            tmp_path = tmp.name

                        text = self.file_extractor.extract_text(tmp_path)
                        if text:
                            extracted_texts.append(f"--- Content from {url} ---\n{text}")

                        os.unlink(tmp_path)
                except Exception as e:
                    extracted_texts.append(f"Error extracting from {url}: {str(e)}")

        return "\n\n".join(extracted_texts) if extracted_texts else ""

    async def _verify_stellar(self, submission: SubmissionInput) -> dict:
        """Verify Stellar account and contract on-chain"""
        stellar_data = {}

        if submission.stellar_address:
            print(f"   🔗 Verifying Stellar account: {submission.stellar_address[:8]}...")
            stellar_data["account"] = await self.stellar_verifier.verify_account(submission.stellar_address)

        if submission.contract_id:
            print(f"   📜 Verifying Soroban contract: {submission.contract_id[:8]}...")
            stellar_data["contract"] = await self.stellar_verifier.verify_contract(submission.contract_id)

            # Also fetch contract events
            events = await self.stellar_verifier.get_contract_events(submission.contract_id)
            if events.get("event_count", 0) > 0:
                stellar_data["contract_events"] = events

        return stellar_data

    def _format_repo_evidence(self, analysis: dict, submission: SubmissionInput):
        """Format repo analysis into structured evidence sections"""
        if not analysis:
            return (
                "No repository analysis available.",
                "No Soroban analysis available.",
                "No source code samples available.",
                "No code quality metrics available.",
                None,
            )

        # Main repo evidence
        cloc = analysis.get("cloc", {})
        repo_evidence = f"""
Repository Statistics:
- Total files: {cloc.get('total_files', 0)}
- Total lines: {cloc.get('total_lines', 0)} (code: {cloc.get('code_lines', 0)}, comments: {cloc.get('comment_lines', 0)}, blank: {cloc.get('blank_lines', 0)})
- Languages: {json.dumps(cloc.get('languages', {}), indent=2)}
- Language line counts: {json.dumps(cloc.get('language_lines', {}), indent=2)}
- Primary language: {analysis.get('primary_language', 'Unknown')}

Complexity Analysis:
{json.dumps(analysis.get('complexity', [])[:15], indent=2)}

Project Structure:
{json.dumps(analysis.get('project_structure', {}), indent=2)}

Git History:
{json.dumps(analysis.get('git_history', {}), indent=2)}

Dependencies:
{json.dumps(analysis.get('dependency_analysis', {}), indent=2)}

Test Analysis:
{json.dumps(analysis.get('test_analysis', {}), indent=2)}

Security Scan:
{json.dumps(analysis.get('security_scan', {}), indent=2)}
"""

        # Soroban-specific evidence
        soroban = analysis.get("soroban_analysis", {})
        if soroban.get("is_soroban_project"):
            soroban_evidence = f"""
Soroban Project: YES
Contracts Found: {soroban.get('contracts_found', 0)}
Contract Files: {json.dumps(soroban.get('contract_files', []), indent=2)}

Security Checklist:
{json.dumps(soroban.get('security_checklist', {}), indent=2)}

Quality Signals:
{json.dumps(soroban.get('quality_signals', []), indent=2)}

Issues Found:
{json.dumps(soroban.get('issues', []), indent=2)}

Patterns Detected:
{json.dumps(soroban.get('patterns_detected', {}), indent=2)}
"""
        else:
            soroban_evidence = f"Soroban Project: {'NO — no Soroban contracts detected in repository' if analysis else 'No repo analyzed'}"

        # Source code samples
        samples = analysis.get("source_code_samples", {})
        if samples:
            source_parts = []
            for filepath, content in samples.items():
                source_parts.append(f"### File: {filepath}\n```\n{content}\n```")
            source_code = "\n\n".join(source_parts)
        else:
            source_code = "No source code samples extracted."

        # Code quality summary
        test_analysis = analysis.get("test_analysis", {})
        git_history = analysis.get("git_history", {})
        project_structure = analysis.get("project_structure", {})
        dep_analysis = analysis.get("dependency_analysis", {})
        security = analysis.get("security_scan", {})

        code_quality_summary = f"""
Has Tests: {test_analysis.get('has_tests', False)} ({test_analysis.get('test_file_count', 0)} test files, ratio: {test_analysis.get('test_to_code_ratio', 0)})
Test Frameworks: {', '.join(test_analysis.get('test_frameworks_detected', [])) or 'None detected'}
Has CI/CD: {project_structure.get('has_ci_cd', False)} ({', '.join(project_structure.get('ci_cd_type', [])) or 'None'})
Has Documentation: {project_structure.get('has_documentation', False)}
Has License: {project_structure.get('has_license', False)}
Has Docker: {project_structure.get('has_docker', False)}
Dependencies: {dep_analysis.get('dependency_count', 0)} total
Stellar Dependencies: {', '.join(dep_analysis.get('stellar_dependencies', [])) or 'None'}
Commits: {git_history.get('total_commits', 0)}
Contributors: {git_history.get('contributor_count', 0)}
Development Duration: {git_history.get('development_duration_days', 0)} days
Security Issues: {security.get('severity_summary', {}).get('critical', 0)} critical, {security.get('severity_summary', {}).get('warning', 0)} warnings
"""

        # Build CodeQualityMetrics object
        complexity_data = analysis.get("complexity", [])
        avg_rank = "N/A"
        if complexity_data:
            ranks = [c.get("rank", "N/A") for c in complexity_data if c.get("rank") != "N/A"]
            if ranks:
                avg_rank = max(set(ranks), key=ranks.count)

        code_metrics = CodeQualityMetrics(
            total_files=cloc.get("total_files", 0),
            total_lines=cloc.get("total_lines", 0),
            languages=cloc.get("languages", {}),
            has_tests=test_analysis.get("has_tests", False),
            test_file_count=test_analysis.get("test_file_count", 0),
            has_ci_cd=project_structure.get("has_ci_cd", False),
            has_documentation=project_structure.get("has_documentation", False),
            has_license=project_structure.get("has_license", False),
            has_dependency_manifest=len(dep_analysis.get("manifests_found", [])) > 0,
            primary_language=analysis.get("primary_language"),
            soroban_contract_detected=soroban.get("is_soroban_project", False),
            smart_contract_count=soroban.get("contracts_found", 0),
            rust_unsafe_blocks=soroban.get("patterns_detected", {}).get("unsafe_block", 0),
            security_patterns_found=soroban.get("quality_signals", []),
            security_issues_found=[i for i in soroban.get("issues", [])],
            dependency_count=dep_analysis.get("dependency_count", 0),
            commit_count=git_history.get("total_commits", 0),
            contributor_count=git_history.get("contributor_count", 0),
            avg_complexity_rank=avg_rank,
        )

        return repo_evidence, soroban_evidence, source_code, code_quality_summary, code_metrics

    def _format_stellar_evidence(self, stellar_data: dict):
        """Format stellar verification into evidence sections"""
        if not stellar_data:
            return "No on-chain verification provided.", "No contract events available."

        stellar_evidence = json.dumps(
            {k: v for k, v in stellar_data.items() if k != "contract_events"},
            indent=2, default=str
        )

        contract_events = "No contract events available."
        if "contract_events" in stellar_data:
            contract_events = json.dumps(stellar_data["contract_events"], indent=2, default=str)

        return stellar_evidence, contract_events

    def _calculate_evidence_completeness(self, submission, repo_result, file_result, stellar_result) -> float:
        """Calculate how much evidence is available (0-1 scale)"""
        score = 0.0
        max_score = 0.0

        # GitHub repo (weight: 35%)
        max_score += 0.35
        if repo_result:
            score += 0.15  # repo cloned
            if repo_result.get("soroban_analysis", {}).get("is_soroban_project"):
                score += 0.10  # soroban contracts found
            if repo_result.get("source_code_samples"):
                score += 0.05  # source code extracted
            if repo_result.get("test_analysis", {}).get("has_tests"):
                score += 0.05  # tests found

        # File content (weight: 15%)
        max_score += 0.15
        if file_result:
            score += 0.15

        # On-chain verification (weight: 25%)
        max_score += 0.25
        if stellar_result:
            if stellar_result.get("account", {}).get("exists"):
                score += 0.12
            if stellar_result.get("contract", {}).get("status") == "VERIFIED_ON_NETWORK":
                score += 0.13

        # README (weight: 10%)
        max_score += 0.10
        if submission.readme_content and len(submission.readme_content) > 100:
            score += 0.10

        # Demo links (weight: 15%)
        max_score += 0.15
        if submission.demo_video_url:
            score += 0.08
        if submission.live_demo_url:
            score += 0.07

        return round(min(score / max_score, 1.0), 2) if max_score > 0 else 0.0

    async def _call_claude_with_retry(self, prompt: str, max_retries: int = 2) -> HackathonGradingResult:
        """Call Claude API with retry logic and robust JSON extraction"""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                response_text = response.content[0].text

                # Robust JSON extraction
                result_data = self._extract_json(response_text)

                # Validate and create result
                result = HackathonGradingResult(**result_data)
                return result

            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON on attempt {attempt + 1}: {e}"
                print(f"   ⚠️ {last_error}")
                if attempt < max_retries:
                    print(f"   🔄 Retrying...")
            except Exception as e:
                last_error = f"Error on attempt {attempt + 1}: {e}"
                print(f"   ⚠️ {last_error}")
                if attempt < max_retries:
                    print(f"   🔄 Retrying...")

        raise RuntimeError(f"Grading failed after {max_retries + 1} attempts. Last error: {last_error}")

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from Claude's response, handling markdown wrappers and extra text"""
        # Try direct parse first
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        json_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_block:
            try:
                return json.loads(json_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object boundaries
        start = text.find('{')
        if start != -1:
            # Find the matching closing brace
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            break

        raise json.JSONDecodeError("Could not extract valid JSON from response", text, 0)

    def calculate_weighted_score(self, scores: dict) -> float:
        """Calculate weighted overall score"""
        weights = {
            'innovation': 0.25,
            'technical_execution': 0.25,
            'stellar_integration': 0.20,
            'ux_design': 0.15,
            'completeness': 0.15
        }

        total = sum(scores.get(criterion, 0) * weight for criterion, weight in weights.items())
        return round(total, 2)
