from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from thb_input.config import get_settings
from thb_input.extract.errors import ExtractError, ExtractErrorCode
from thb_input.extract.llm import OpenAICompatibleExtractLLMClient
from thb_input.extract.schemas import ExtractRequest, ExtractResult
from thb_input.extract.service import ExtractService

router = APIRouter(prefix="/extract", tags=["extract"])


@lru_cache
def get_extract_service() -> ExtractService:
    settings = get_settings()
    return ExtractService(
        OpenAICompatibleExtractLLMClient(settings),
        validation_retries=settings.extract_validation_retries,
    )


@router.post("", response_model=ExtractResult)
def create_extract_result(
    request: ExtractRequest,
    service: Annotated[ExtractService, Depends(get_extract_service)],
) -> ExtractResult:
    try:
        return service.process(request)
    except ExtractError as exc:
        raise HTTPException(
            status_code=_status_for_error(exc.code),
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc


def _status_for_error(code: ExtractErrorCode) -> int:
    if code is ExtractErrorCode.LLM_CONFIGURATION_ERROR:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if code is ExtractErrorCode.LLM_TIMEOUT:
        return status.HTTP_504_GATEWAY_TIMEOUT
    if code is ExtractErrorCode.LLM_CALL_FAILED:
        return status.HTTP_502_BAD_GATEWAY
    return status.HTTP_422_UNPROCESSABLE_CONTENT
