import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.engine import HackathonGradingEngine
from app.models import SubmissionInput

load_dotenv()

async def test_grading():
    print("🚀 Testing AI Grading System (Hackathon)\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return

    # Create engine
    engine = HackathonGradingEngine(api_key=api_key)
    
    # Sample submission
    submission = SubmissionInput(
        submission_id="test_001",
        team_name="Stellar Builders",
        project_name="PayStream",
        tagline="Real-time payment streaming on Stellar",
        description="""
        PayStream is a decentralized payment streaming protocol built on Stellar.
        It allows users to create continuous payment streams for subscriptions,
        salaries, or any recurring payment use case.
        
        Key features:
        - Stream payments per second
        - Pause/resume streams
        - Withdraw accrued funds anytime
        - Built with Soroban smart contracts
        """,
        github_url="https://github.com/team/paystream",
        readme_content="""
        # PayStream
        
        ## Installation
        npm install
        
        ## Smart Contract
        The core streaming logic is in contracts/stream.rs
        
        ## Frontend
        Built with Next.js and Stellar SDK
        """,
        demo_video_url="https://youtube.com/watch?v=demo123",
        live_demo_url="https://paystream-demo.vercel.app"
    )
    
    print(f"📝 Grading submission: {submission.project_name}")
    print(f"   by: {submission.team_name}\n")
    
    # Grade it
    try:
        result = await engine.grade_submission(
            submission=submission,
            hackathon_name="Stellar DeFi Sprint 2026"
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
