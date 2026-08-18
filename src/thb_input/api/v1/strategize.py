from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from thb_input.config import get_settings
from thb_input.strategize.errors import StrategizeError, StrategizeErrorCode
from thb_input.strategize.llm import OpenAICompatibleStrategizeLLMClient
from thb_input.strategize.schemas import StrategizeRequest, StrategizeResult
from thb_input.strategize.service import StrategizeService

router = APIRouter(prefix="/strategize", tags=["strategize"])


@lru_cache
def get_strategize_service() -> StrategizeService:
    settings = get_settings()
    return StrategizeService(
        OpenAICompatibleStrategizeLLMClient(settings),
        validation_retries=settings.strategize_validation_retries,
    )


@router.post("", response_model=StrategizeResult)
def create_strategize_result(
    request: StrategizeRequest,
    service: Annotated[StrategizeService, Depends(get_strategize_service)],
) -> StrategizeResult:
    try:
        return service.process(request)
    except StrategizeError as exc:
        raise HTTPException(
            status_code=_status_for_error(exc.code),
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc


def _status_for_error(code: StrategizeErrorCode) -> int:
    if code is StrategizeErrorCode.LLM_CONFIGURATION_ERROR:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if code is StrategizeErrorCode.LLM_TIMEOUT:
        return status.HTTP_504_GATEWAY_TIMEOUT
    if code is StrategizeErrorCode.LLM_CALL_FAILED:
        return status.HTTP_502_BAD_GATEWAY
    return status.HTTP_422_UNPROCESSABLE_CONTENT
