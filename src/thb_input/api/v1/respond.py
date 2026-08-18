from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from thb_input.config import get_settings
from thb_input.respond.errors import RespondError, RespondErrorCode
from thb_input.respond.llm import OpenAICompatibleRespondLLMClient
from thb_input.respond.schemas import RespondRequest, RespondResult
from thb_input.respond.service import RespondService

router = APIRouter(prefix="/respond", tags=["respond"])


@lru_cache
def get_respond_service() -> RespondService:
    settings = get_settings()
    return RespondService(
        OpenAICompatibleRespondLLMClient(settings),
        validation_retries=settings.respond_validation_retries,
    )


@router.post("", response_model=RespondResult)
def create_respond_result(
    request: RespondRequest,
    service: Annotated[RespondService, Depends(get_respond_service)],
) -> RespondResult:
    try:
        return service.process(request)
    except RespondError as exc:
        raise HTTPException(
            status_code=_status_for_error(exc.code),
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc


def _status_for_error(code: RespondErrorCode) -> int:
    if code is RespondErrorCode.LLM_CONFIGURATION_ERROR:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if code is RespondErrorCode.LLM_TIMEOUT:
        return status.HTTP_504_GATEWAY_TIMEOUT
    if code is RespondErrorCode.LLM_CALL_FAILED:
        return status.HTTP_502_BAD_GATEWAY
    return status.HTTP_422_UNPROCESSABLE_CONTENT
