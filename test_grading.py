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
    
    # Hackathon Context
    hack_context = HackathonContext(
        name="Stellar DeFi Sprint 2026",
        description="Build innovative DeFi applications on the Stellar network using Soroban smart contracts.",
        judging_criteria="""
        1. Innovation (25%): How unique and creative is the solution?
        2. Technical Execution (25%): Quality and completeness of the code.
        3. Stellar Integration (20%): How well does it use Stellar/Soroban?
        4. UX/Design (15%): User experience and visual polish.
        5. Completeness (15%): Is it a working demo?
        """,
        duration_hours=48
    )

    # Sample submission (using a real public repo for testing)
    submission = SubmissionInput(
        submission_id="test_001",
        team_name="Stellar Builders",
        project_name="Stellar Python SDK",
        tagline="Python library for communicating with a Stellar Horizon server",
        description="The Stellar Python SDK is a library for communicating with a Stellar Horizon server.",
        github_url="https://github.com/StellarCN/py-stellar-base.git",
        stellar_address="GB5XDSF6IOE57KHC7N7S3T7S3A5A5A5A5A5A5A5A5A5A5A5A5A5A5A5A", # Sample testnet address
        readme_content="# py-stellar-base\n\nPython library for Stellar...",
        demo_video_url="https://youtube.com/watch?v=demo123",
        live_demo_url="https://paystream-demo.vercel.app",
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
