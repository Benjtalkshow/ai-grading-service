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

# Evidence Provided
## GitHub Repository Analysis
{repo_analysis}

## Extracted Content/Files
{extracted_content}

## Stellar/Blockchain Evidence
{stellar_evidence}

---

# Stellar Expert Knowledge (Grading Guidelines)
When evaluating Stellar/Soroban projects, pay special attention to:

## 1. Soroban Smart Contract Security
- **Missing Authorization**: Ensure `require_auth()` is used on privileged operations.
- **Reinitialization**: Check if `initialize` functions have guards to prevent being called twice.
- **Checked Arithmetic**: Look for `.checked_add()`, `.checked_sub()`, etc., instead of raw operators.
- **Storage Management**: Verify correct use of `Instance`, `Persistent`, and `Temporary` storage, and check for `extend_ttl()` calls.
- **Contract Size**: Efficiency check (aiming for under 64KB).

## 2. Stellar Integration Best Practices
- **Trustlines**: Proper handling of `op_no_trust` errors and trustline creation.
- **Sequence Numbers**: Robust handling of transaction sequences.
- **Simulation**: Use of transaction simulation before submission.
- **Network Passphrase**: Correct identification of Testnet vs Mainnet.

## 3. Common Pitfalls
- Use of `#![no_std]` in contracts.
- Proper event emission for auditable state changes.
- Validation of external contract calls (allowlists).

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
    submission: SubmissionInput,
    repo_analysis: str = "No deep repository analysis available.",
    extracted_content: str = "No additional files extracted.",
    stellar_evidence: str = "No on-chain verification provided."
) -> str:
    """Build the grading prompt with submission, context, and evidence"""
    context = submission.hackathon_context
    
    # Default values if context is missing
    hack_name = context.name if context else "Stellar Hackathon"
    hack_desc = context.description if context else "Build innovative applications on Stellar"
    hack_criteria = context.judging_criteria if context else "Standard hackathon criteria (Innovation, Tech, UX, etc.)"
    hack_duration = context.duration_hours if context else 48

    return HACKATHON_GRADING_PROMPT_V1.format(
        hackathon_name=hack_name,
        hackathon_description=hack_desc,
        judging_criteria=hack_criteria,
        duration_hours=hack_duration,
        repo_analysis=repo_analysis,
        extracted_content=extracted_content,
        stellar_evidence=stellar_evidence,
        team_name=submission.team_name,
        project_name=submission.project_name,
        tagline=submission.tagline,
        description=submission.description,
        github_url=submission.github_url or "Not provided",
        readme_content=submission.readme_content or "Not provided",
        demo_video_url=submission.demo_video_url or "Not provided",
        live_demo_url=submission.live_demo_url or "Not provided"
    )
