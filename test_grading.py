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
    
    # Hackathon Context (Real: Stellar Meridian 2024)
    hack_context = HackathonContext(
        name="Stellar Meridian 2024 Global Hackathon",
        description="Build innovative applications on the Stellar network using Soroban, Passkeys, and the latest developer tools to solve real-world problems.",
        judging_criteria="""
        1. Innovation (25%): Uniqueness and creativity of the solution.
        2. Technical Execution (25%): Quality of the Soroban contracts, security, and overall code.
        3. User Experience (20%): Interface design and ease of use (e.g., using Passkeys).
        4. Impact (15%): Real-world potential and problem-solving value.
        5. Presentation (15%): Clarity of the demo and pitch.
        """,
        duration_hours=72
    )

    # Sample submission (Real: Strooper Wallet - Meridian 2024 Winner)
    submission = SubmissionInput(
        submission_id="meridian_2024_01",
        team_name="Strooper Team",
        project_name="Strooper Wallet",
        tagline="A smart, non-custodial Stellar wallet as a Telegram Mini-App",
        description="""
        Strooper Wallet is a non-custodial wallet integrated directly into Telegram as a Mini-App.
        It uses Stellar's Passkeys and Soroban smart contracts to allow users to secure and send
        assets directly within their favorite messaging app without the need for traditional seed phrases.
        """,
        github_url="https://github.com/JoseCToscano/strooper-wallet.git",
        stellar_address="GDJWSUHK636G7S3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K3E7K", # Placeholder for real testnet address
        demo_video_url="https://www.youtube.com/watch?v=real_meridian_demo",
        live_demo_url="https://t.me/strooper_bot",
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
