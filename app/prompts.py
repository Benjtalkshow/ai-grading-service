from .models import SubmissionInput

HACKATHON_GRADING_PROMPT_V1 = """
You are an expert hackathon judge evaluating a project submission.

# Hackathon Context
Event: {hackathon_name}
Duration: {duration_hours} hours
Description: {hackathon_description}

# Judging Criteria
{judging_criteria}

---

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

Evaluate the submission based on the **Judging Criteria** provided above. 
If criteria are not explicitly weighted in the text, use the standard 1-10 scale for each criterion.

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
- Consider the {duration_hours}-hour timeframe (rough edges are expected)
- Value working demos over perfect code
- Reward innovation even if execution is imperfect
- If information is missing, note it and score conservatively
"""

def build_grading_prompt(
    submission: SubmissionInput
) -> str:
    """Build the grading prompt with submission and context data"""
    context = submission.hackathon_context
    
    # Default values if context is missing for some reason
    hack_name = context.name if context else "Stellar Hackathon"
    hack_desc = context.description if context else "Build innovative applications on Stellar"
    hack_criteria = context.judging_criteria if context else "Standard hackathon criteria (Innovation, Tech, UX, etc.)"
    hack_duration = context.duration_hours if context else 48

    return HACKATHON_GRADING_PROMPT_V1.format(
        hackathon_name=hack_name,
        hackathon_description=hack_desc,
        judging_criteria=hack_criteria,
        duration_hours=hack_duration,
        team_name=submission.team_name,
        project_name=submission.project_name,
        tagline=submission.tagline,
        description=submission.description,
        github_url=submission.github_url or "Not provided",
        readme_content=submission.readme_content or "Not provided",
        demo_video_url=submission.demo_video_url or "Not provided",
        live_demo_url=submission.live_demo_url or "Not provided"
    )
