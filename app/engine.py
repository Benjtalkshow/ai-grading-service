from anthropic import Anthropic
import json
import os
from typing import Optional
from dotenv import load_dotenv

from .models import HackathonGradingResult, SubmissionInput
from .prompts import build_grading_prompt

load_dotenv()

class HackathonGradingEngine:
    """AI-powered hackathon submission grading"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
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
        
        # Build prompt
        prompt = build_grading_prompt(
            submission=submission
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
