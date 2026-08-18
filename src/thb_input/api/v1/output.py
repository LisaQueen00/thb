from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from thb_input.output.errors import OutputError
from thb_input.output.schemas import OutputRequest, OutputResult
from thb_input.output.service import OutputService

router = APIRouter(prefix="/output", tags=["output"])


@lru_cache
def get_output_service() -> OutputService:
    return OutputService()


@router.post("", response_model=OutputResult)
def create_output(
    request: OutputRequest,
    service: Annotated[OutputService, Depends(get_output_service)],
) -> OutputResult:
    try:
        return service.process(request)
    except OutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": exc.code.value, "message": exc.message},
        ) from exc
