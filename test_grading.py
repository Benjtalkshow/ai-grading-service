import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.engine import HackathonGradingEngine
from app.models import SubmissionInput, HackathonContext

load_dotenv()


def print_result(result):
    """Pretty-print the grading result"""
    print("\n" + "=" * 60)
    print("GRADING COMPLETE")
    print("=" * 60)

    print(f"\n  Overall Score: {result.overall_score}/10")
    print(f"  Recommendation: {result.recommendation}")
    print(f"  Confidence: {result.confidence_level}")
    if result.confidence_reasoning:
        print(f"  Reason: {result.confidence_reasoning}")
    print(f"  Evidence Completeness: {result.evidence_completeness * 100:.0f}%")

    print(f"\n--- Criterion Scores ---")
    for name, criterion in [
        ("Innovation", result.innovation),
        ("Technical Execution", result.technical_execution),
        ("Stellar Integration", result.stellar_integration),
        ("UX/Design", result.ux_design),
        ("Completeness", result.completeness),
    ]:
        print(f"\n  {name}: {criterion.score}/10")
        print(f"    {criterion.reasoning[:150]}...")
        if criterion.sub_scores:
            sub_str = ", ".join(f"{k}: {v}" for k, v in criterion.sub_scores.items())
            print(f"    Sub-scores: {sub_str}")
        if criterion.strengths:
            for s in criterion.strengths[:2]:
                print(f"    + {s}")
        if criterion.weaknesses:
            for w in criterion.weaknesses[:2]:
                print(f"    - {w}")

    if result.code_quality_metrics:
        m = result.code_quality_metrics
        print(f"\n--- Code Quality Metrics ---")
        print(f"  Files: {m.total_files} | Lines: {m.total_lines} | Primary: {m.primary_language}")
        print(f"  Tests: {'Yes' if m.has_tests else 'No'} ({m.test_file_count} files) | CI/CD: {'Yes' if m.has_ci_cd else 'No'}")
        print(f"  Soroban: {'Yes' if m.soroban_contract_detected else 'No'} ({m.smart_contract_count} contracts)")
        print(f"  Commits: {m.commit_count} | Contributors: {m.contributor_count}")
        print(f"  Complexity: {m.avg_complexity_rank} | Dependencies: {m.dependency_count}")
        if m.security_patterns_found:
            print(f"  Security +: {', '.join(m.security_patterns_found[:3])}")
        if m.security_issues_found:
            print(f"  Security -: {', '.join(m.security_issues_found[:3])}")

    if result.technical_depth_assessment:
        print(f"\n--- Technical Depth ---")
        print(f"  {result.technical_depth_assessment}")

    if result.stellar_specific_findings:
        print(f"\n--- Stellar Findings ---")
        for finding in result.stellar_specific_findings[:5]:
            print(f"  * {finding}")

    if result.red_flags:
        print(f"\n--- Red Flags ---")
        for flag in result.red_flags:
            print(f"  ! {flag}")

    if result.plagiarism_indicators:
        print(f"\n--- Plagiarism Check ---")
        for indicator in result.plagiarism_indicators:
            print(f"  [{indicator.confidence}] {indicator.flag_type}: {indicator.detail}")

    if result.standout_features:
        print(f"\n--- Standout Features ---")
        for feature in result.standout_features:
            print(f"  * {feature}")

    if result.improvement_suggestions:
        print(f"\n--- Improvement Suggestions ---")
        for suggestion in result.improvement_suggestions:
            print(f"  > {suggestion}")

    print(f"\n{'=' * 60}")

    # Assertions
    assert 0 <= result.overall_score <= 10, f"Score out of range: {result.overall_score}"
    assert result.recommendation in ("STRONG_ACCEPT", "ACCEPT", "BORDERLINE", "REJECT")
    assert result.confidence_level in ("HIGH", "MEDIUM", "LOW")
    assert 0 <= result.evidence_completeness <= 1
    print("All assertions passed!\n")


async def test_soroswap():
    """
    Test 1: Soroswap — a real, mature Soroban AMM DEX by PaltaLabs.
    Public repo: https://github.com/soroswap/core
    Funded by the Stellar Community Fund. Contains Factory, Router, and Pair contracts.
    """
    print("\n" + "#" * 60)
    print("TEST 1: Soroswap (Real Soroban AMM DEX)")
    print("#" * 60)

    hack_context = HackathonContext(
        name="Stellar Community Fund - DeFi Round",
        description="Build decentralized finance protocols on Stellar using Soroban smart contracts. Projects should demonstrate real financial innovation and deep Stellar integration.",
        judging_criteria="""
        1. Financial Innovation (25%): Novelty and soundness of the DeFi mechanism.
        2. Technical Excellence (25%): Code quality, security, testing, and Soroban best practices.
        3. Stellar Integration (20%): Depth and correctness of Stellar/Soroban usage.
        4. UX/Design (15%): User experience for interacting with the protocol.
        5. Completeness (15%): How finished and deployable the project is.
        """,
        duration_hours=720,
        tracks=["DeFi", "Infrastructure"],
        required_technologies=["Soroban"],
        bonus_criteria=["Multi-hop routing", "Flash loan support", "Oracle integration"],
    )

    submission = SubmissionInput(
        submission_id="scf_soroswap_01",
        team_name="PaltaLabs",
        project_name="Soroswap",
        tagline="The first AMM DEX protocol on Stellar/Soroban",
        description="""
        Soroswap is the first automated market maker (AMM) protocol built natively on
        Stellar using Soroban smart contracts. It implements a Uniswap V2-style constant
        product market maker with Factory, Router, and Pair contracts. Users can create
        liquidity pools for any Soroban token pair, provide liquidity, and swap tokens
        in a fully decentralized and permissionless way. The protocol includes multi-hop
        routing for optimal swap paths and has been deployed on Stellar testnet.
        """,
        github_url="https://github.com/soroswap/core",
        demo_video_url="https://www.youtube.com/watch?v=soroswap_demo",
        live_demo_url="https://app.soroswap.finance",
        hackathon_context=hack_context,
        track="DeFi",
        team_size=4,
    )

    engine = HackathonGradingEngine()
    result = await engine.grade_submission(submission=submission)
    print_result(result)
    return result


async def test_soroban_did():
    """
    Test 2: Soroban DID Contract — a real decentralized identity contract by kommitters.
    Public repo: https://github.com/kommitters/soroban-did-contract
    A smaller, focused project — good for testing calibration on a simpler submission.
    """
    print("\n" + "#" * 60)
    print("TEST 2: Soroban DID Contract (Decentralized Identity)")
    print("#" * 60)

    hack_context = HackathonContext(
        name="Stellar Hackathon - Identity & Infrastructure",
        description="Build identity, credential, or infrastructure tools on Stellar using Soroban. Projects should solve real problems in decentralized identity or provide foundational tools for the ecosystem.",
        judging_criteria="""
        1. Innovation (25%): Originality of the approach to decentralized identity on Stellar.
        2. Technical Execution (25%): Code quality, security, and Soroban best practices.
        3. Stellar Integration (20%): Meaningful use of Stellar/Soroban features.
        4. UX/Design (15%): Developer experience and API design.
        5. Completeness (15%): How functional and documented the project is.
        """,
        duration_hours=168,
        tracks=["Identity", "Infrastructure"],
        required_technologies=["Soroban"],
    )

    submission = SubmissionInput(
        submission_id="hack_did_01",
        team_name="Kommitters",
        project_name="Soroban DID Contract",
        tagline="Decentralized Identifiers (DIDs) on Stellar via Soroban",
        description="""
        A Soroban smart contract implementing W3C Decentralized Identifiers (DIDs) on the
        Stellar network. Allows creating DIDs, managing DID documents, and updating DID
        attributes entirely on-chain. The contract provides a foundation for self-sovereign
        identity on Stellar, enabling verifiable credentials and decentralized authentication
        without relying on centralized identity providers.
        """,
        github_url="https://github.com/kommitters/soroban-did-contract",
        hackathon_context=hack_context,
        track="Identity",
        team_size=2,
    )

    engine = HackathonGradingEngine()
    result = await engine.grade_submission(submission=submission)
    print_result(result)
    return result


async def main():
    print("=" * 60)
    print("  Boundless AI Grading Service v2.0 — Integration Tests")
    print("  Using REAL public Stellar/Soroban repositories")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("\nError: ANTHROPIC_API_KEY not set in .env")
        return

    # Run test 1: Soroswap (complex, mature project — should score well)
    result1 = await test_soroswap()

    # Run test 2: Soroban DID (smaller, focused project — tests calibration)
    result2 = await test_soroban_did()

    # Cross-check: the more mature project should generally score higher
    print("\n" + "=" * 60)
    print("  COMPARISON SUMMARY")
    print("=" * 60)
    print(f"  Soroswap:          {result1.overall_score}/10 ({result1.recommendation})")
    print(f"  Soroban DID:       {result2.overall_score}/10 ({result2.recommendation})")
    print(f"  Score difference:  {abs(result1.overall_score - result2.overall_score):.2f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
