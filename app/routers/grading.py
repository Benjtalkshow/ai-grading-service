from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time
import traceback

from ..engine import HackathonGradingEngine
from ..models import SubmissionInput, HackathonGradingResult

router = APIRouter(prefix="/grading", tags=["grading"])


class GradeSubmissionRequest(BaseModel):
    submission: SubmissionInput


class GradeSubmissionResponse(BaseModel):
    success: bool
    result: HackathonGradingResult
    processing_time_seconds: float


class BatchGradeRequest(BaseModel):
    submissions: List[SubmissionInput]


class BatchGradeResponseItem(BaseModel):
    submission_id: str
    success: bool
    result: Optional[HackathonGradingResult] = None
    error: Optional[str] = None
    processing_time_seconds: float


class BatchGradeResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[BatchGradeResponseItem]
    total_processing_time_seconds: float


@router.post("/hackathon", response_model=GradeSubmissionResponse)
async def grade_hackathon_submission(request: GradeSubmissionRequest):
    """
    Grade a single hackathon submission using AI.
    Returns detailed scoring with evidence-based reasoning.
    """
    start_time = time.time()

    try:
        engine = HackathonGradingEngine()
        result = await engine.grade_submission(submission=request.submission)

        processing_time = time.time() - start_time

        return GradeSubmissionResponse(
            success=True,
            result=result,
            processing_time_seconds=round(processing_time, 2)
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"AI grading service error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")


@router.post("/hackathon/batch", response_model=BatchGradeResponse)
async def batch_grade_submissions(request: BatchGradeRequest):
    """
    Grade multiple hackathon submissions sequentially.
    Returns results for each submission, continuing even if individual submissions fail.
    """
    total_start = time.time()
    results = []
    successful = 0
    failed = 0

    engine = HackathonGradingEngine()

    for submission in request.submissions:
        start_time = time.time()
        try:
            result = await engine.grade_submission(submission=submission)
            processing_time = time.time() - start_time
            results.append(BatchGradeResponseItem(
                submission_id=submission.submission_id,
                success=True,
                result=result,
                processing_time_seconds=round(processing_time, 2)
            ))
            successful += 1
        except Exception as e:
            processing_time = time.time() - start_time
            results.append(BatchGradeResponseItem(
                submission_id=submission.submission_id,
                success=False,
                error=str(e),
                processing_time_seconds=round(processing_time, 2)
            ))
            failed += 1

    total_time = time.time() - total_start

    return BatchGradeResponse(
        total=len(request.submissions),
        successful=successful,
        failed=failed,
        results=results,
        total_processing_time_seconds=round(total_time, 2)
    )
