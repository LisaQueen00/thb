from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from thb_input.meaning import MeaningResult
from thb_input.workflow import THBWorkflow, WorkflowError

router = APIRouter(prefix="/thb", tags=["thb"])


class THBRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_message: str
    context: str | None = None


class THBPublicResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meaning: str


def to_public_response(result: MeaningResult) -> THBPublicResponse:
    return THBPublicResponse(meaning=result.meaning)


@lru_cache
def get_workflow() -> THBWorkflow:
    return THBWorkflow()


@router.post("", response_model=THBPublicResponse)
def run_thb(
    request: THBRequest,
    workflow: Annotated[THBWorkflow, Depends(get_workflow)],
) -> THBPublicResponse:
    try:
        return to_public_response(workflow.run(request.source_message, request.context))
    except WorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": exc.code, "stage": exc.stage, "message": exc.message},
        ) from exc
