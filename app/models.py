from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict
from datetime import datetime


class EvidenceCitation(BaseModel):
    """A specific piece of evidence supporting a score"""
    source: str = Field(description="Where the evidence came from (e.g., 'GitHub repo', 'README', 'on-chain data')")
    detail: str = Field(description="The specific evidence found")
    impact: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(description="How this evidence affects the score")


class CodeQualityMetrics(BaseModel):
    """Quantitative code quality indicators extracted from repo analysis"""
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = Field(default_factory=dict)
    has_tests: bool = False
    test_file_count: int = 0
    has_ci_cd: bool = False
    has_documentation: bool = False
    has_license: bool = False
    has_dependency_manifest: bool = False
    primary_language: Optional[str] = None
    soroban_contract_detected: bool = False
    smart_contract_count: int = 0
    rust_unsafe_blocks: int = 0
    security_patterns_found: List[str] = Field(default_factory=list)
    security_issues_found: List[str] = Field(default_factory=list)
    dependency_count: int = 0
    commit_count: int = 0
    contributor_count: int = 0
    avg_complexity_rank: str = "N/A"


class CriterionScore(BaseModel):
    """Individual criterion score with evidence-backed reasoning"""
    score: float = Field(ge=0, le=10, description="Score from 0-10")
    reasoning: str = Field(min_length=10, description="Detailed explanation with evidence citations")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    evidence: List[EvidenceCitation] = Field(default_factory=list, description="Specific evidence supporting the score")
    sub_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown sub-scores within this criterion (e.g., for technical_execution: {'architecture': 7, 'code_quality': 8, 'testing': 5})"
    )


class PlagiarismIndicator(BaseModel):
    """Indicators of potential plagiarism or rule violations"""
    flag_type: Literal[
        "BOILERPLATE_HEAVY",
        "TEMPLATE_FORK",
        "COPY_PASTE_DETECTED",
        "COMMIT_HISTORY_SUSPICIOUS",
        "MISMATCHED_COMPLEXITY",
        "PRE_EXISTING_WORK",
        "NONE"
    ]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    detail: str


class HackathonGradingResult(BaseModel):
    """Complete grading result for a hackathon submission"""
    overall_score: float = Field(ge=0, le=10)

    # Criterion scores
    innovation: CriterionScore
    technical_execution: CriterionScore
    stellar_integration: CriterionScore
    ux_design: CriterionScore
    completeness: CriterionScore

    # Code quality metrics (populated from repo analysis)
    code_quality_metrics: Optional[CodeQualityMetrics] = None

    # Advanced analysis
    red_flags: List[str] = Field(default_factory=list)
    plagiarism_indicators: List[PlagiarismIndicator] = Field(default_factory=list)
    standout_features: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)

    # Comparative context
    technical_depth_assessment: str = Field(
        default="",
        description="Summary of the technical depth and sophistication of the project"
    )
    stellar_specific_findings: List[str] = Field(
        default_factory=list,
        description="Specific findings related to Stellar/Soroban implementation quality"
    )

    recommendation: Literal["STRONG_ACCEPT", "ACCEPT", "BORDERLINE", "REJECT"]
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    confidence_reasoning: str = Field(
        default="",
        description="Why the confidence level was assigned (e.g., limited evidence, thorough analysis)"
    )

    # Metadata
    graded_at: datetime = Field(default_factory=datetime.utcnow)
    grading_model: str = "claude-sonnet-4-6"
    evidence_completeness: float = Field(
        default=0.0,
        ge=0, le=1,
        description="0-1 score indicating how much evidence was available for grading"
    )

    @field_validator("overall_score", mode="before")
    @classmethod
    def round_overall_score(cls, v):
        return round(float(v), 2)


class HackathonContext(BaseModel):
    """Specific details about the hackathon"""
    name: str = Field(description="Name of the hackathon")
    description: str = Field(description="Overall description and theme")
    judging_criteria: str = Field(description="Specific judging criteria and weights")
    duration_hours: Optional[int] = Field(default=48, description="Duration of the event")
    tracks: List[str] = Field(default_factory=list, description="Hackathon tracks/categories")
    required_technologies: List[str] = Field(default_factory=list, description="Technologies that must be used")
    bonus_criteria: List[str] = Field(default_factory=list, description="Bonus criteria for extra points")


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
    track: Optional[str] = Field(None, description="Which hackathon track this submission is for")
    team_size: Optional[int] = Field(None, description="Number of team members")
    prior_submissions: Optional[List[str]] = Field(default_factory=list, description="IDs of prior submissions for cross-reference")
