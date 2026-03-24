from anthropic import Anthropic
import json
import os
from typing import Optional
from dotenv import load_dotenv

from .models import HackathonGradingResult, SubmissionInput
import tempfile
from .prompts import build_grading_prompt
from .services.extractor import RepoAnalyzer
from .services.file_reader import FileExtractor
from .services.stellar_verifier import StellarVerifier
import httpx

load_dotenv()

class HackathonGradingEngine:
    """AI-powered hackathon submission grading"""
    
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
        Grade a hackathon submission using Claude
        
        Args:
            submission: The submission data (includes hackathon_context)
            
        Returns:
            HackathonGradingResult with scores and feedback
        """
        
        # 1. Advanced Analysis (Code/Repo)
        repo_evidence = "No deep repository analysis available."
        if submission.github_url:
            analysis = await self.repo_analyzer.analyze_repo(submission.github_url)
            if "error" not in analysis:
                repo_evidence = f"""
                Lines of Code stats: {json.dumps(analysis['cloc'], indent=2)}
                Complexity analysis: {json.dumps(analysis['complexity'], indent=2)}
                """
                # Use extracted readme if better
                if analysis.get('readme') and len(analysis['readme']) > (len(submission.readme_content or "")):
                    submission.readme_content = analysis['readme']

        # 2. File Content Extraction
        extracted_content = "No additional files extracted."
        if submission.file_urls:
            extracted_texts = []
            async with httpx.AsyncClient() as client:
                for url in submission.file_urls:
                    try:
                        resp = await client.get(url, timeout=10.0)
                        if resp.status_code == 200:
                            # Save temp file to extract
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp:
                                tmp.write(resp.content)
                                tmp_path = tmp.name
                            
                            text = self.file_extractor.extract_text(tmp_path)
                            if text:
                                extracted_texts.append(f"--- Content from {url} ---\n{text}")
                            
                            os.unlink(tmp_path)
                    except Exception as e:
                        extracted_texts.append(f"Error extracting from {url}: {str(e)}")
            
            if extracted_texts:
                extracted_content = "\n\n".join(extracted_texts)

        # 3. Stellar/Blockchain Verification
        stellar_evidence = "No on-chain verification provided."
        stellar_data = {}
        
        if submission.stellar_address:
            stellar_data["account"] = await self.stellar_verifier.verify_account(submission.stellar_address)
        
        if submission.contract_id:
            stellar_data["contract"] = await self.stellar_verifier.verify_contract(submission.contract_id)
            
        if stellar_data:
            stellar_evidence = json.dumps(stellar_data, indent=2)

        # 4. Build prompt with evidence
        prompt = build_grading_prompt(
            submission=submission,
            repo_analysis=repo_evidence,
            extracted_content=extracted_content,
            stellar_evidence=stellar_evidence
        )
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temp for consistent scoring
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            
            # Parse JSON (Claude should return valid JSON)
            result_data = json.loads(response_text)
            
            # Validate and create result object
            result = HackathonGradingResult(**result_data)
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude returned invalid JSON: {e}\nResponse: {response_text}")
        except Exception as e:
            raise RuntimeError(f"Grading failed: {e}")
    
    def calculate_weighted_score(self, scores: dict) -> float:
        """Calculate weighted overall score (utility method)"""
        weights = {
            'innovation': 0.25,
            'technical_execution': 0.25,
            'stellar_integration': 0.20,
            'ux_design': 0.15,
            'completeness': 0.15
        }
        
        total = sum(scores[criterion] * weight for criterion, weight in weights.items())
        return round(total, 2)
