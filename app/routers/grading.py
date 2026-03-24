from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import time

from ..engine import HackathonGradingEngine
from ..models import SubmissionInput, HackathonGradingResult

# Note: We are using a relative import here, but in main.py we'll need to be careful.
# Actually, let's use absolute imports for the app package.

router = APIRouter(prefix="/grading", tags=["grading"])

class GradeSubmissionRequest(BaseModel):
    hackathon_name: str
    submission: SubmissionInput

class GradeSubmissionResponse(BaseModel):
    success: bool
    result: HackathonGradingResult
    processing_time_seconds: float

@router.post("/hackathon", response_model=GradeSubmissionResponse)
async def grade_hackathon_submission(request: GradeSubmissionRequest):
    """
    Grade a hackathon submission using AI.
    The caller (NestJS) should provide the submission data.
    """
    start_time = time.time()
    
    try:
        engine = HackathonGradingEngine()
        result = await engine.grade_submission(
            submission=request.submission,
            hackathon_name=request.hackathon_name
        )
        
        processing_time = time.time() - start_time
        
        return GradeSubmissionResponse(
            success=True,
            result=result,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")
