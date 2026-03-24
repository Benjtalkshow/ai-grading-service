from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class CriterionScore(BaseModel):
    """Individual criterion score"""
    score: float = Field(ge=0, le=10, description="Score from 0-10")
    reasoning: str = Field(min_length=10, description="Detailed explanation")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

class HackathonGradingResult(BaseModel):
    """Complete grading result for a hackathon submission"""
    overall_score: float = Field(ge=0, le=10)
    
    # Criterion scores
    innovation: CriterionScore
    technical_execution: CriterionScore
    stellar_integration: CriterionScore
    ux_design: CriterionScore
    completeness: CriterionScore
    
    # Additional info
    red_flags: List[str] = Field(default_factory=list)
    standout_features: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    recommendation: Literal["STRONG_ACCEPT", "ACCEPT", "BORDERLINE", "REJECT"]
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    
    # Metadata
    graded_at: datetime = Field(default_factory=datetime.utcnow)
    grading_model: str = "claude-3-5-sonnet"

class HackathonContext(BaseModel):
    """Specific details about the hackathon"""
    name: str = Field(description="Name of the hackathon")
    description: str = Field(description="Overall description and theme")
    judging_criteria: str = Field(description="Specific judging criteria and weights")
    duration_hours: Optional[int] = Field(default=48, description="Duration of the event")

class SubmissionInput(BaseModel):
    """Input data for grading"""
    submission_id: str
    team_name: str
    project_name: str
    tagline: str
    description: str
    github_url: Optional[str] = None
    demo_video_url: Optional[str] = None
    live_demo_url: Optional[str] = None
    file_urls: List[str] = Field(default_factory=list, description="URLs to documents (PDF, Docx) for analysis")
    stellar_address: Optional[str] = Field(None, description="Stellar wallet address for verification")
    contract_id: Optional[str] = Field(None, description="Soroban contract ID for verification")
    readme_content: Optional[str] = None
    hackathon_context: Optional[HackathonContext] = None
