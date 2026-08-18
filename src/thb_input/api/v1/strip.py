from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from thb_input.config import get_settings
from thb_input.schemas.input import InputRecord
from thb_input.strip.errors import StripError, StripErrorCode
from thb_input.strip.llm import OpenAICompatibleLLMClient
from thb_input.strip.schemas import StripResult
from thb_input.strip.service import StripService

router = APIRouter(prefix="/strip", tags=["strip"])


@lru_cache
def get_strip_service() -> StripService:
    settings = get_settings()
    return StripService(
        OpenAICompatibleLLMClient(settings),
        validation_retries=settings.strip_validation_retries,
    )


@router.post("", response_model=StripResult)
def create_strip_result(
    canonical_input: InputRecord,
    service: Annotated[StripService, Depends(get_strip_service)],
) -> StripResult:
    try:
        return service.process(canonical_input)
    except StripError as exc:
        status_code = _status_for_error(exc.code)
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc


def _status_for_error(code: StripErrorCode) -> int:
    if code is StripErrorCode.LLM_CONFIGURATION_ERROR:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if code is StripErrorCode.LLM_TIMEOUT:
        return status.HTTP_504_GATEWAY_TIMEOUT
    if code is StripErrorCode.LLM_CALL_FAILED:
        return status.HTTP_502_BAD_GATEWAY
    return status.HTTP_422_UNPROCESSABLE_CONTENT
