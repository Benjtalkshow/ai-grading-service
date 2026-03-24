import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.engine import HackathonGradingEngine
from app.models import SubmissionInput, HackathonContext

load_dotenv()

async def test_grading():
    print("🚀 Testing AI Grading System (Hackathon)\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return

    # Create engine
    engine = HackathonGradingEngine(api_key=api_key)
    
    # Hackathon Context (Real: Stellar Community Fund / DeFi Challenge)
    hack_context = HackathonContext(
        name="Stellar DeFi Challenge 2024",
        description="Build advanced DeFi protocols on Stellar using Soroban smart contracts. Focus on AMMs, lending, or liquidity provisioning.",
        judging_criteria="""
        1. Financial Innovation (30%): Novelty of the DeFi mechanism.
        2. Technical Excellence (30%): Quality, security, and optimization of Soroban contracts.
        3. Integration (20%): Depth of Stellar network feature usage.
        4. Documentation (20%): Clarity of technical documentation and README.
        """,
        duration_hours=120
    )

    # Sample submission (Real: Pact DeFi - Audited Stellar Protocol)
    submission = SubmissionInput(
        submission_id="scf_pact_01",
        team_name="Pact Team",
        project_name="Pact DeFi",
        tagline="A decentralized automated market maker (AMM) on Stellar",
        description="""
        Pact is a decentralized exchange (DEX) built on Stellar using Soroban.
        It implements a constant product market maker (CPMM) model, allowing users
        to swap assets and provide liquidity in a permissionless way.
        """,
        github_url="https://github.com/pact-fi/pact-stellar-contracts.git",
        stellar_address="GDJWSUHK636G7S3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K", # Placeholder
        demo_video_url="https://www.youtube.com/watch?v=pact_demo",
        live_demo_url="https://pact.fi",
        hackathon_context=hack_context
    )
    
    print(f"📝 Grading submission: {submission.project_name}")
    print(f"   by: {submission.team_name}\n")
    
    # Grade it
    try:
        result = await engine.grade_submission(
            submission=submission
        )
        
        print("✅ Grading Complete!\n")
        print(f"Overall Score: {result.overall_score}/10")
        print(f"Recommendation: {result.recommendation}")
        print(f"Confidence: {result.confidence_level}\n")
        
        print("Criterion Scores:")
        print(f"  Innovation:          {result.innovation.score}/10")
        print(f"  Technical Execution: {result.technical_execution.score}/10")
        print(f"  Stellar Integration: {result.stellar_integration.score}/10")
        print(f"  UX/Design:           {result.ux_design.score}/10")
        print(f"  Completeness:        {result.completeness.score}/10")
        print()
        
        print("Standout Features:")
        for feature in result.standout_features:
            print(f"  ✨ {feature}")
        print()
        
        print("Improvement Suggestions:")
        for suggestion in result.improvement_suggestions:
            print(f"  💡 {suggestion}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_grading())
