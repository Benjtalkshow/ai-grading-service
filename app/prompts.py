from .models import SubmissionInput

HACKATHON_GRADING_PROMPT_V1 = """
You are an expert hackathon judge evaluating a Stellar blockchain project.

# Hackathon Context
Event: {hackathon_name}
Duration: 48 hours
Theme: Build innovative applications on Stellar

# Submission Details
Team: {team_name}
Project: {project_name}
Tagline: {tagline}

## Description
{description}

## GitHub Repository
{github_url}

## README Content
{readme_content}

## Demo/Links
Demo Video: {demo_video_url}
Live Demo: {live_demo_url}

---

# Grading Instructions

Score this submission on 5 criteria (1-10 scale each):

## 1. Innovation (Weight: 25%)
Does this project introduce novel ideas, creative solutions, or unique approaches?
Consider:
- Originality of concept
- Creative use of Stellar features
- Differentiation from existing solutions

## 2. Technical Execution (Weight: 25%)
How well is the project implemented technically?
Consider:
- Code quality (based on README/description)
- Completeness of implementation
- Technical sophistication

## 3. Stellar Integration (Weight: 20%)
How effectively does the project use Stellar blockchain?
Consider:
- Proper use of Stellar features
- Integration depth (not just surface-level)
- Smart contract usage (if applicable)

## 4. UX/Design (Weight: 15%)
How polished and user-friendly is the product?
Consider:
- Clarity of demo/description
- User experience considerations
- Visual design (if visible in demo)

## 5. Completeness & Feasibility (Weight: 15%)
Is this a functional demo that could realistically ship?
Consider:
- Feature completeness
- Realistic scope for 48 hours
- Post-hackathon viability

---

# Output Format

You MUST respond with valid JSON in this exact structure:

{{
  "overall_score": <float 0-10, weighted average>,
  "innovation": {{
    "score": <float 1-10>,
    "reasoning": "<2-3 sentences explaining the score>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"]
  }},
  "technical_execution": {{
    "score": <float 1-10>,
    "reasoning": "<2-3 sentences>",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."]
  }},
  "stellar_integration": {{
    "score": <float 1-10>,
    "reasoning": "<2-3 sentences>",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."]
  }},
  "ux_design": {{
    "score": <float 1-10>,
    "reasoning": "<2-3 sentences>",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."]
  }},
  "completeness": {{
    "score": <float 1-10>,
    "reasoning": "<2-3 sentences>",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."]
  }},
  "red_flags": ["<any concerns about plagiarism, rule violations, etc.>"],
  "standout_features": ["<what makes this project impressive>"],
  "improvement_suggestions": ["<constructive feedback>"],
  "recommendation": "<STRONG_ACCEPT | ACCEPT | BORDERLINE | REJECT>",
  "confidence_level": "<HIGH | MEDIUM | LOW>"
}}

# Important Guidelines
- Be objective and evidence-based
- Consider the 48-hour timeframe (rough edges are expected)
- Value working demos over perfect code
- Reward innovation even if execution is imperfect
- If information is missing, note it and score conservatively
- Overall score should be weighted: (Innovation×0.25) + (Technical×0.25) + (Stellar×0.20) + (UX×0.15) + (Completeness×0.15)
"""

def build_grading_prompt(
    hackathon_name: str,
    submission: SubmissionInput
) -> str:
    """Build the grading prompt with submission data"""
    return HACKATHON_GRADING_PROMPT_V1.format(
        hackathon_name=hackathon_name,
        team_name=submission.team_name,
        project_name=submission.project_name,
        tagline=submission.tagline,
        description=submission.description,
        github_url=submission.github_url or "Not provided",
        readme_content=submission.readme_content or "Not provided",
        demo_video_url=submission.demo_video_url or "Not provided",
        live_demo_url=submission.live_demo_url or "Not provided"
    )
